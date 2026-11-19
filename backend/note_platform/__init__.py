# Compatibility patch for CheckConstraint between Django versions (Django 4.2 check= vs Django 5.1+ condition=)
try:
    from django.db.models.constraints import CheckConstraint

    _orig_check_constraint_init = CheckConstraint.__init__

    def _compat_check_constraint_init(self, *args, **kwargs):
        try:
            return _orig_check_constraint_init(self, *args, **kwargs)
        except TypeError as err:
            err_msg = str(err)
            if "unexpected keyword argument 'check'" in err_msg and "check" in kwargs:
                kwargs["condition"] = kwargs.pop("check")
                return _orig_check_constraint_init(self, *args, **kwargs)
            elif "unexpected keyword argument 'condition'" in err_msg and "condition" in kwargs:
                kwargs["check"] = kwargs.pop("condition")
                return _orig_check_constraint_init(self, *args, **kwargs)
            raise

    CheckConstraint.__init__ = _compat_check_constraint_init
except Exception:
    pass
