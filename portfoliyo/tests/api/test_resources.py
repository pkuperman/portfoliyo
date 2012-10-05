"""Tests for API resources."""
from django.core.urlresolvers import reverse
import mock

from portfoliyo.api import resources
from portfoliyo.tests import factories, utils



class TestProfileResource(object):
    def test_dehydrate_email(self):
        email = 'foo@example.com'
        bundle = mock.Mock()
        bundle.obj.user.email = email

        assert resources.ProfileResource().dehydrate_email(bundle) == email


    def list_url(self):
        """Get profile list API url."""
        return reverse(
            'api_dispatch_list',
            kwargs={
                'resource_name': 'user',
                'api_name': 'v1',
                },
            )


    def detail_url(self, profile):
        """Get detail API url for given profile."""
        return reverse(
            'api_dispatch_detail',
            kwargs={
                'resource_name': 'user',
                'api_name': 'v1',
                'pk': profile.pk,
                },
            )


    def test_only_see_same_school_users(self, no_csrf_client):
        """Users can only see other users from same school in API."""
        p1 = factories.ProfileFactory.create()
        factories.ProfileFactory.create()
        hero = factories.ProfileFactory.create(
            school_staff=True, school=p1.school)

        response = no_csrf_client.get(self.list_url(), user=hero.user)
        objects = response.json['objects']

        assert len(objects) == 2
        assert set([p['id'] for p in objects]) == set([p1.pk, hero.pk])


    def test_village_uri(self, no_csrf_client):
        """Each profile has a village_uri in the API response."""
        s = factories.ProfileFactory.create(school_staff=True)
        village_url = reverse('village', kwargs={'student_id': s.id})

        response = no_csrf_client.get(self.list_url(), user=s.user)

        assert response.json['objects'][0]['village_uri'] == village_url



    def test_filter_by_elder(self, no_csrf_client):
        """Can filter profiles by elders."""
        rel = factories.RelationshipFactory.create()
        rel2 = factories.RelationshipFactory.create(
            school=rel.elder.school, from_profile__school_staff=True)

        response = no_csrf_client.get(
            self.list_url() + '?elders=' + str(rel.elder.pk),
            user=rel2.elder.user,
            )
        objects = response.json['objects']

        assert len(objects) == 1
        assert objects[0]['id'] == rel.student.pk


    def test_filter_by_student(self, no_csrf_client):
        """Can filter profiles by students."""
        rel = factories.RelationshipFactory.create()
        rel2 = factories.RelationshipFactory.create(
            school=rel.elder.school, from_profile__school_staff=True)

        response = no_csrf_client.get(
            self.list_url() + '?students=' + str(rel.student.pk),
            user=rel2.elder.user,
            )
        objects = response.json['objects']

        assert len(objects) == 1
        assert objects[0]['id'] == rel.elder.pk


    def test_filter_by_elder_in_group(self, no_csrf_client):
        """Can filter profiles by group elder memberships."""
        s1 = factories.ProfileFactory.create()
        s2 = factories.ProfileFactory.create(school=s1.school)
        group = factories.GroupFactory.create(owner__school=s1.school)
        group.students.add(s1)
        group.elders.add(s2)

        response = no_csrf_client.get(
            self.list_url() + '?elder_in_groups=' + str(group.pk),
            user=factories.ProfileFactory.create(
                school=s1.school, school_staff=True).user,
            )
        objects = response.json['objects']

        assert len(objects) == 1
        assert objects[0]['id'] == s2.pk


    def test_filter_by_student_in_group(self, no_csrf_client):
        """Can filter profiles by group student memberships."""
        s1 = factories.ProfileFactory.create()
        s2 = factories.ProfileFactory.create(school=s1.school)
        group = factories.GroupFactory.create(owner__school=s1.school)
        group.students.add(s1)
        group.elders.add(s2)

        response = no_csrf_client.get(
            self.list_url() + '?student_in_groups=' + str(group.pk),
            user=factories.ProfileFactory.create(
                school=s1.school, school_staff=True).user,
            )
        objects = response.json['objects']

        assert len(objects) == 1
        assert objects[0]['id'] == s1.pk


    def test_delete_profile(self, no_csrf_client):
        """A school-staff user from same school may delete another profile."""
        p = factories.ProfileFactory.create()
        p2 = factories.ProfileFactory.create(school_staff=True, school=p.school)

        no_csrf_client.delete(self.detail_url(p), user=p2.user, status=204)

        assert utils.refresh(p).deleted


    def test_delete_profile_csrf_protected(self, client):
        """Deletion is CSRF-protected."""
        p = factories.ProfileFactory.create()
        p2 = factories.ProfileFactory.create(school_staff=True, school=p.school)

        client.delete(self.detail_url(p), user=p2.user, status=403)


    def test_delete_profile_requires_school_staff(self, no_csrf_client):
        """A non-school-staff user may not delete a profile."""
        p = factories.ProfileFactory.create()
        p2 = factories.ProfileFactory.create(
            school_staff=False, school=p.school)

        no_csrf_client.delete(self.detail_url(p), user=p2.user, status=403)

        assert not utils.refresh(p).deleted


    def test_delete_profile_requires_same_school(self, no_csrf_client):
        """A school-staff user from another school may not delete a profile."""
        p = factories.ProfileFactory.create()
        p2 = factories.ProfileFactory.create(school_staff=True)

        no_csrf_client.delete(self.detail_url(p), user=p2.user, status=404)

        assert not utils.refresh(p).deleted



class TestGroupResource(object):
    def list_url(self):
        """Get list API url."""
        return reverse(
            'api_dispatch_list',
            kwargs={'resource_name': 'group', 'api_name': 'v1'},
            )


    def detail_url(self, group):
        """Get detail API url for given group."""
        return reverse(
            'api_dispatch_detail',
            kwargs={'resource_name': 'group', 'api_name': 'v1', 'pk': group.pk},
            )


    def test_only_see_my_groups(self, no_csrf_client):
        """User can only see their own groups in API, not even same-school."""
        g1 = factories.GroupFactory.create(owner__school_staff=True)
        factories.GroupFactory.create(owner__school=g1.owner.school)

        response = no_csrf_client.get(self.list_url(), user=g1.owner.user)
        objects = response.json['objects']

        assert len(objects) == 1
        assert objects[0]['id'] == g1.pk


    def test_delete_group(self, no_csrf_client):
        """Owner of a group can delete it."""
        group = factories.GroupFactory.create(owner__school_staff=True)

        no_csrf_client.delete(
            self.detail_url(group), user=group.owner.user, status=204)

        assert utils.refresh(group).deleted


    def test_delete_group_requires_owner(self, no_csrf_client):
        """Non-owner cannot delete a group, even if school staff."""
        group = factories.GroupFactory.create()
        profile = factories.ProfileFactory.create(
            school_staff=True, school=group.owner.school)

        no_csrf_client.delete(
            self.detail_url(group), user=profile.user, status=404)

        assert not utils.refresh(group).deleted


    def test_students_uri(self, no_csrf_client):
        g = factories.GroupFactory.create(owner__school_staff=True)
        students_url = reverse(
            'api_dispatch_list',
            kwargs={'resource_name': 'user', 'api_name': 'v1'},
            ) + '?student_in_groups=' + str(g.pk)

        response = no_csrf_client.get(self.list_url(), user=g.owner.user)

        assert response.json['objects'][0]['students_uri'] == students_url
