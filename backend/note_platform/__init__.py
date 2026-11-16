# Compatibility patch for CheckConstraint between Django versions (Django 4.2 check= vs Django 5.1+ condition=)
try:
    from django.db.models.constraints import CheckConstraint

    _orig_check_constraint_init = CheckConstraint.__init__

    def _compat_check_constraint_init(self, *args, **kwargs):
        if "check" in kwargs and "condition" not in kwargs:
            kwargs["condition"] = kwargs.pop("check")
        elif "condition" in kwargs and "check" not in kwargs:
            # If running on an older Django where condition is not accepted, fallback to check
            try:
                return _orig_check_constraint_init(self, *args, **kwargs)
            except TypeError:
                kwargs["check"] = kwargs.pop("condition")
                return _orig_check_constraint_init(self, *args, **kwargs)
        return _orig_check_constraint_init(self, *args, **kwargs)

    CheckConstraint.__init__ = _compat_check_constraint_init
except Exception:
    pass
