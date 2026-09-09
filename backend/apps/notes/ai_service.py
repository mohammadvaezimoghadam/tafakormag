import os
import json
import logging
import urllib.request
import urllib.error
from django.conf import settings
from django.db.models import Q
from apps.notes.models import Topic, Post, TopicFAQ, TopicChatSession, TopicChatMessage

logger = logging.getLogger(__name__)


class TopicRAGService:
    @staticmethod
    def retrieve_topic_context(topic: Topic, query: str, max_posts: int = 8, max_faqs: int = 5):
        query_cleaned = (query or "").strip()
        words = [w for w in query_cleaned.split() if len(w) > 2]

        # 1. Retrieve FAQs
        faq_qs = TopicFAQ.objects.filter(topic=topic, is_published=True)
        if words:
            faq_q_filter = Q()
            for w in words:
                faq_q_filter |= Q(question__icontains=w) | Q(answer__icontains=w)
            matched_faqs = list(faq_qs.filter(faq_q_filter)[:max_faqs])
            if len(matched_faqs) < max_faqs:
                existing_ids = {f.id for f in matched_faqs}
                additional_faqs = list(faq_qs.exclude(id__in=existing_ids)[:max_faqs - len(matched_faqs)])
                matched_faqs.extend(additional_faqs)
        else:
            matched_faqs = list(faq_qs[:max_faqs])

        # 2. Retrieve Posts
        post_qs = Post.objects.filter(topic=topic).exclude(content__isnull=True).exclude(content__exact="")
        if words:
            post_q_filter = Q()
            for w in words:
                post_q_filter |= Q(content__icontains=w)
            matched_posts = list(post_qs.filter(post_q_filter).order_by("-created_at")[:max_posts])
            if len(matched_posts) < max_posts:
                existing_ids = {p.id for p in matched_posts}
                recent_posts = list(post_qs.exclude(id__in=existing_ids).order_by("-created_at")[:max_posts - len(matched_posts)])
                matched_posts.extend(recent_posts)
        else:
            matched_posts = list(post_qs.order_by("-created_at")[:max_posts])

        # 3. Assemble sources
        sources = []
        for faq in matched_faqs:
            sources.append({
                "type": "faq",
                "id": faq.id,
                "title": faq.question,
                "preview": faq.answer[:90] + ("..." if len(faq.answer) > 90 else "")
            })
        for post in matched_posts:
            clean_content = (post.content or "").strip().replace("\n", " ")
            sources.append({
                "type": "post",
                "id": post.id,
                "title": f"نوشته #{post.id}",
                "author": post.author.phone if post.author else "کاربر تاپیک",
                "preview": clean_content[:90] + ("..." if len(clean_content) > 90 else ""),
                "created_at": post.created_at.strftime("%Y/%m/%d %H:%M")
            })

        return {
            "topic_name": topic.name,
            "topic_description": topic.description or "",
            "faqs": matched_faqs,
            "posts": matched_posts,
            "sources": sources
        }

    @staticmethod
    def _local_fallback_answer(topic: Topic, query: str, context: dict) -> str:
        query_lower = query.lower().strip()
        faqs = context["faqs"]
        posts = context["posts"]

        # Check for direct FAQ match
        for f in faqs:
            if any(word in f.question.lower() for word in query_lower.split() if len(word) > 2):
                return (
                    f"**پاسخ رسمی بر اساس سوالات متداول تاپیک:**\n\n"
                    f"> **سوال:** {f.question}\n\n"
                    f"{f.answer}\n\n"
                    f"*منبع: بخش سوالات متداول رسمی تاپیک «{topic.name}»*"
                )

        # Check for matching posts
        matching_posts = []
        for p in posts:
            if any(word in (p.content or "").lower() for word in query_lower.split() if len(word) > 2):
                matching_posts.append(p)

        if matching_posts:
            first_post = matching_posts[0]
            summary_lines = [
                f"با بررسی محتوای تاپیک **{topic.name}**، اطلاعات مرتبط با پرسش شما یافت شد:\n",
                f"{first_post.content}\n"
            ]
            if len(matching_posts) > 1:
                summary_lines.append("\n**سایر مطالب مرتبط در تاپیک:**")
                for mp in matching_posts[1:3]:
                    summary_lines.append(f"- {mp.content[:120]}...")
            return "\n".join(summary_lines)

        # General topic overview fallback
        faq_preview = ""
        if faqs:
            faq_preview = "\n\n**موضوعات پرتکرار تاپیک:**\n" + "\n".join([f"- {faq.question}" for faq in faqs[:3]])

        return (
            f"سلام! من دستیار هوشمند تاپیک **{topic.name}** هستم.\n\n"
            f"{topic.description or 'در این تاپیک به بحث و تبادل نظر درباره موضوعات مرتبط می‌پردازیم.'}"
            f"{faq_preview}\n\n"
            f"پرسش شما در داده‌های موجود به طور صریح یافت نشد. می‌توانید از سوالات متداول فوق استفاده فرمایید یا سوال خود را دقیق‌تر مطرح نمایید."
        )

    @classmethod
    def generate_topic_answer(cls, topic: Topic, query: str, history: list = None, session: TopicChatSession = None):
        history = history or []
        context = cls.retrieve_topic_context(topic, query)

        api_key = getattr(settings, "AI_API_KEY", os.getenv("AI_API_KEY", ""))
        api_base = getattr(settings, "AI_API_BASE_URL", os.getenv("AI_API_BASE_URL", "https://openrouter.ai/api/v1")).rstrip("/")
        model = getattr(settings, "AI_MODEL", os.getenv("AI_MODEL", "google/gemma-4-31b-it:free"))

        # تصحیح خودکار آدرس اندپوینت OpenRouter در صورتی که کاربر لینک مدل یا آدرس بدون نسخه را وارد کرده باشد
        if "openrouter.ai" in api_base and not api_base.endswith("/api/v1"):
            api_base = "https://openrouter.ai/api/v1"

        if api_key:
            faq_text = "\n".join([f"سوال: {f.question}\nپاسخ: {f.answer}" for f in context["faqs"]])
            posts_text = "\n".join([f"نوشته #{p.id} ({p.created_at.strftime('%Y-%m-%d')}): {p.content}" for p in context["posts"]])

            system_prompt = (
                f"شما دستیار هوشمند رسمی تاپیک «{topic.name}» در پلتفرم تفکر هستید.\n"
                f"توضیحات تاپیک:\n{topic.description or 'ندارد'}\n\n"
                f"اطلاعات بازیابی‌شده تاپیک:\n"
                f"--- سوالات متداول تاپیک ---\n{faq_text or 'هیچ سوالی ثبت نشده'}\n\n"
                f"--- نوشته‌ها و پیام‌های اخیر تاپیک ---\n{posts_text or 'هیچ نوشته‌ای ثبت نشده'}\n\n"
                f"دستورالعمل‌ها:\n"
                f"۱. فقط بر اساس اطلاعات تاپیک بالا پاسخ دهید.\n"
                f"۲. زبان پاسخ باید فارسی روان، محترمانه و با فرمت‌بندی مرتب مارک‌داون باشد.\n"
                f"۳. اگر پاسخ در اطلاعات نبود، صادقانه اعلام کنید که در محتوای تاپیک موجود نیست.\n"
                f"۴. در پایان در صورت ارتباط، اشاره مختصری به نوشته‌ها یا سوالات منبع داشته باشید."
            )

            messages = [{"role": "system", "content": system_prompt}]
            for h in history[-4:]:
                if h.get("role") in ("user", "assistant") and h.get("content"):
                    messages.append({"role": h["role"], "content": h["content"]})
            messages.append({"role": "user", "content": query})

            payload = {
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": 800
            }

            # در صورتی که مدل اوپن‌روتر و از نوع رایگان باشد، مدل‌های جایگزین برای جلوگیری از Rate-Limit قرار داده می‌شود (حداکثر ۳ مدل)
            if "openrouter.ai" in api_base:
                if ":free" in model:
                    payload["models"] = [
                        model,
                        "nvidia/nemotron-3.5-lightning:free",
                        "google/gemma-4-26b-a4b-it:free"
                    ][:3]
                else:
                    payload["model"] = model
            else:
                payload["model"] = model

            endpoint_url = api_base if api_base.endswith("/chat/completions") else f"{api_base}/chat/completions"
            req = urllib.request.Request(
                endpoint_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "Tafakor-AI/1.0",
                    "HTTP-Referer": "https://tafakor.ir",
                    "X-Title": "Tafakor Topic Assistant",
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=15) as response:
                    res_body = json.loads(response.read().decode("utf-8"))
                    answer = res_body["choices"][0]["message"]["content"].strip()
                    return {
                        "answer": answer,
                        "sources": context["sources"]
                    }
            except urllib.error.HTTPError as e:
                try:
                    err_msg = e.read().decode("utf-8")
                except Exception:
                    err_msg = str(e)
                logger.warning(f"LLM API HTTPError {e.code}: {err_msg}. Falling back to local synthesizer.")
            except Exception as e:
                logger.warning(f"LLM API call failed: {e}. Falling back to local synthesizer.")

        # Local synthesizer fallback
        answer = cls._local_fallback_answer(topic, query, context)
        return {
            "answer": answer,
            "sources": context["sources"]
        }
