"""Portfoliyo API resources."""
from django.core.urlresolvers import reverse
from django.core.exceptions import ObjectDoesNotExist
from tastypie import constants, fields
from tastypie.authorization import ReadOnlyAuthorization
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource

from portfoliyo.api.authentication import SessionAuthentication
from portfoliyo.api.authorization import (
    ProfileAuthorization, GroupAuthorization)
from portfoliyo import model


class PortfoliyoResource(ModelResource):
    """
    Common default values for all resources.

    Also supports per-row authorization, for detail requests only, in the
    simplest way possible without switching to this incomplete branch of
    Tastypie:
    https://github.com/toastdriven/django-tastypie/compare/master...perms

    This implementation assumes that all action methods (e.g. get_detail,
    post_list, etc) will all eventually call obj_get_list/cached_obj_get_list
    or obj_get/cached_obj_get at least once passing the request object. It also
    assumes the authorization check is cheap enough that it's ok to potentially
    perform the authorization check twice in case of a cache miss when used a
    cached_* method.

    """
    class Meta:
        authentication = SessionAuthentication()
        authorization = ReadOnlyAuthorization()
        allowed_methods = ['get']
        # @@@ this should be high enough to never cause pagination in our use
        # cases, but we should have a better solution here than a magic number
        # (like maybe a custom paginator class that doesn't paginate?)
        limit = 200


    def wrap_view(self, view):
        """Undo csrf-exempt on view wrapper; we want session-csrf to run."""
        wrapper = super(PortfoliyoResource, self).wrap_view(view)
        wrapper.csrf_exempt = False
        return wrapper


    def is_authorized(self, request, object=None):
        """Neuter built-in to avoid failure when dispatch calls it w/o obj."""
        pass


    def real_is_authorized(self, request, object=None):
        """Provide real is_authorized method under different name."""
        return super(PortfoliyoResource, self).is_authorized(request, object)


    def cached_obj_get_list(self, request=None, **kwargs):
        """Get the object list (maybe from cache), then verify authorization."""
        objs = super(PortfoliyoResource, self).cached_obj_get_list(
            request, **kwargs)
        if request is not None:
            self.real_is_authorized(request)
        return objs


    def obj_get_list(self, request=None, **kwargs):
        """Get the object list, then verify authorization."""
        objs = super(PortfoliyoResource, self).obj_get_list(request, **kwargs)
        if request is not None:
            self.real_is_authorized(request)
        return objs


    def cached_obj_get(self, request=None, **kwargs):
        """Get the object (perhaps from cache) then verify authorization."""
        obj = super(PortfoliyoResource, self).cached_obj_get(request, **kwargs)
        if request is not None:
            self.real_is_authorized(request, obj)
        return obj


    def obj_get(self, request=None, **kwargs):
        """Get the object, then verify authorization."""
        obj = super(PortfoliyoResource, self).obj_get(request, **kwargs)
        if request is not None:
            self.real_is_authorized(request, obj)
        return obj




class SoftDeletedResource(PortfoliyoResource):
    """Base Resource class for soft-deletes (sets deleted flag)."""
    def obj_delete_list(self, request=None, **kwargs):
        """Soft-delete a list of objects."""
        base_object_list = self.get_object_list(request).filter(**kwargs)
        authed_object_list = self.apply_authorization_limits(
            request, base_object_list)

        if hasattr(authed_object_list, 'delete'):
            # It's likely a ``QuerySet``. Call ``.update()`` for efficiency.
            authed_object_list.update(deleted=True)
        else:
            for authed_obj in authed_object_list:
                authed_obj.deleted = True
                authed_obj.save()

    def obj_delete(self, request=None, **kwargs):
        """Soft-delete a single object."""
        obj = kwargs.pop('_obj', None)

        if not hasattr(obj, 'save'):
            try:
                obj = self.obj_get(request, **kwargs)
            except ObjectDoesNotExist:
                raise NotFound(
                    "A model instance matching the provided arguments "
                    "could not be found."
                    )

        obj.deleted = True
        obj.save()


    class Meta(PortfoliyoResource.Meta):
        pass




class SimpleToManyField(fields.ToManyField):
    """A to-many field that operates off a simple list-returning property."""
    def dehydrate(self, bundle):
        related = getattr(bundle.obj, self.attribute)

        dehydrated = []

        for obj in related:
            resource = self.get_related_resource(obj)
            related_bundle = Bundle(obj=obj, request=bundle.request)
            dehydrated.append(self.dehydrate_related(related_bundle, resource))

        return dehydrated




class ProfileResource(SoftDeletedResource):
    invited_by = fields.ForeignKey('self', 'invited_by', blank=True, null=True)
    elders = SimpleToManyField('self', 'elders')
    students = SimpleToManyField('self', 'students')
    email = fields.CharField()


    def dehydrate_email(self, bundle):
        return bundle.obj.user.email


    def build_filters(self, filters=None):
        filters = filters or {}

        elders = filters.pop('elders', None)
        students = filters.pop('students', None)
        student_in_groups = filters.pop('student_in_groups', None)
        elder_in_groups = filters.pop('elder_in_groups', None)

        orm_filters = super(ProfileResource, self).build_filters(filters)

        if elders:
            orm_filters['relationships_to__from_profile__in'] = elders
        if students:
            orm_filters['relationships_from__to_profile__in'] = students
        if student_in_groups:
            orm_filters['student_in_groups__in'] = student_in_groups
        if elder_in_groups:
            orm_filters['elder_in_groups__in'] = elder_in_groups

        return orm_filters


    def dehydrate(self, bundle):
        bundle.data['village_uri'] = reverse(
            'village',
            kwargs={'student_id': bundle.obj.id},
            )

        return bundle


    class Meta(SoftDeletedResource.Meta):
        queryset = (
            model.Profile.objects.filter(deleted=False).select_related('user'))
        resource_name = 'user'
        fields = [
            'id',
            'name',
            'email',
            'phone',
            'role',
            'school_staff',
            'code',
            'invited_by',
            'declined',
            'elders',
            'students',
            ]
        filtering = {
            'school_staff': constants.ALL,
            }
        authorization = ProfileAuthorization()
        detail_allowed_methods = ['get', 'delete']



class ElderRelationshipResource(PortfoliyoResource):
    elder = fields.ForeignKey(ProfileResource, 'from_profile', full=True)
    student = fields.ForeignKey(ProfileResource, 'to_profile', full=True)
    relationship = fields.CharField('description_or_role')


    class Meta(PortfoliyoResource.Meta):
        queryset = model.Relationship.objects.filter(
            kind=model.Relationship.KIND.elder).select_related(
            'from_profile', 'to_profile')
        resource_name = 'relationship'
        fields = ['elder', 'student', 'relationship']
        filtering = {
            'elder': ['exact'],
            'student': ['exact'],
            }



class GroupResource(SoftDeletedResource):
    owner = fields.ForeignKey(ProfileResource, 'owner')
    students = fields.ManyToManyField(ProfileResource, 'students')
    elders = fields.ManyToManyField(ProfileResource, 'elders')


    def dehydrate(self, bundle):
        bundle.data['students_uri'] = reverse(
            'api_dispatch_list',
            kwargs={'resource_name': 'user', 'api_name': 'v1'},
            ) + '?student_in_groups=' + str(bundle.obj.id)

        return bundle


    class Meta(SoftDeletedResource.Meta):
        queryset = model.Group.objects.filter(deleted=False)
        resource_name = 'group'
        fields = ['id', 'name', 'owner', 'members']
        filtering = {
            'owner': ['exact'],
            }
        authorization = GroupAuthorization()
        detail_allowed_methods = ['get', 'delete']



class PostResource(PortfoliyoResource):
    author = fields.ForeignKey(ProfileResource, 'author', blank=True, null=True)
    student = fields.ForeignKey(ProfileResource, 'student')


    class Meta(PortfoliyoResource.Meta):
        queryset = model.Post.objects.all()
        resource_name = 'post'
        fields = [
            'id',
            'author',
            'timestamp',
            'student',
            'original_text',
            'html_text',
            'to_sms',
            'from_sms',
            ]
        filtering = {
            'author': ['exact'],
            'student': ['exact'],
            }
