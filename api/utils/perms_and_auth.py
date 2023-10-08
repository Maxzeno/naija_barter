from rest_framework.permissions import BasePermission

class MyBasePerm(BasePermission):
    def check_basic_perm(self, request, view):
        if not request.user.is_active:
            self.message = 'user is not active'
            return False
        if request.user.is_suspended:
            self.message = 'user is suspended'
            return False
        if not request.user.email_confirmed:
            self.message = 'Email not confirmed'
            return False
        return None
    
class MyValidUser(MyBasePerm):
    code = 403

    def has_permission(self, request, view):
        if request.user:
            check_basic_perm = self.check_basic_perm(request, view)
            if check_basic_perm is not None:
                return check_basic_perm
            if request.user.is_authenticated:
                self.code = 200
                self.message = "Successful"
                return True

        self.code = 401
        self.message = "Not Authorized"
        return False


# class MyOwner(MyBasePerm):
#     code = 403

#     def has_permission(self, request, view):
#         if request.user:
#             check_basic_perm = self.check_basic_perm(request, view)
#             if check_basic_perm is not None:
#                 return check_basic_perm
#             if request.user.is_authenticated:
#                 self.code = 200
#                 self.message = "Successful"

#                 try:
#                     obj = view.get_queryset().get(pk=view.kwargs['pk'])
#                 except Exception as e:
#                     return False
#                 return obj == request.user

#         self.code = 401
#         self.message = "Not Authorized"
#         return False
