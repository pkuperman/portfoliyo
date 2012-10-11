"""Tests for village views."""
import datetime

from django.core import mail
from django.core.urlresolvers import reverse
from django.utils.timezone import utc
import mock
import pytest

from portfoliyo.view.village import views

from portfoliyo.tests import factories, utils




class TestDashboard(object):
    def test_dashboard(self, client):
        """Asks user to pick a student."""
        rel = factories.RelationshipFactory(to_profile__name="Student Two")
        factories.RelationshipFactory(
            from_profile=rel.elder, to_profile__name="Student One")
        response = client.get(
            reverse('dashboard'), user=rel.elder.user, status=200)

        response.mustcontain("Please select a student")



class TestAddStudent(object):
    """Tests for add_student view."""
    def test_add_student(self, client):
        """User can add a student."""
        teacher = factories.ProfileFactory.create(school_staff=True)
        form = client.get(
            reverse('add_student'), user=teacher.user).forms['add-student-form']
        form['name'] = "Some Student"
        response = form.submit()

        student = teacher.students[0]

        assert response.status_code == 302, response.body
        assert response['Location'] == utils.location(
            reverse('village', kwargs={'student_id': student.id}))


    def test_add_student_in_group(self, client):
        """User can add a student in a group context."""
        group = factories.GroupFactory.create(owner__school_staff=True)
        form = client.get(
            reverse('add_student_in_group', kwargs={'group_id': group.id }),
            user=group.owner.user,
            ).forms['add-student-form']
        form['name'] = "Some Student"
        response = form.submit()

        student = group.students.get()

        assert response.status_code == 302, response.body
        assert response['Location'] == utils.location(
            reverse('village', kwargs={'student_id': student.id}))


    def test_validation_error(self, client):
        """Name of student must be provided."""
        teacher = factories.ProfileFactory.create(school_staff=True)
        form = client.get(
            reverse('add_student'), user=teacher.user).forms['add-student-form']
        response = form.submit(status=200)

        response.mustcontain("field is required")


    def test_requires_school_staff(self, client):
        """Adding a student requires ``school_staff`` attribute."""
        someone = factories.ProfileFactory.create(school_staff=False)
        response = client.get(
            reverse('add_student'), user=someone.user, status=302).follow()

        response.mustcontain("account doesn't have access"), response.html


    def test_anonymous_user_doesnt_blow_up(self, client):
        """Anonymous user on school-staff-required redirects gracefully."""
        response = client.get(reverse('add_student'), status=302).follow()

        assert not "account doesn't have access" in response.content



class TestEditStudent(object):
    """Tests for edit_student view."""
    def url(self, student=None):
        """Shortcut to get URL of edit-student view."""
        if student is None:
            student = factories.ProfileFactory.create()
        return reverse('edit_student', kwargs={'student_id': student.id})


    def test_edit_student(self, client):
        """User can edit a student."""
        rel = factories.RelationshipFactory.create(
            from_profile__school_staff=True)
        form = client.get(
            self.url(rel.student),
            user=rel.elder.user,
            ).forms['edit-student-form']
        form['name'] = "Some Student"
        response = form.submit(status=302)

        assert response['Location'] == utils.location(
            reverse('village', kwargs={'student_id': rel.student.id}))


    def test_validation_error(self, client):
        """Name of student must be provided."""
        rel = factories.RelationshipFactory.create(
            from_profile__school_staff=True)
        form = client.get(
            self.url(rel.student),
            user=rel.elder.user,
            ).forms['edit-student-form']
        form['name'] = ""
        response = form.submit(status=200)

        response.mustcontain("field is required")


    def test_requires_relationship(self, client):
        """Editing a student requires elder relationship."""
        someone = factories.ProfileFactory.create(school_staff=True)
        client.get(self.url(), user=someone.user, status=404)


    def test_requires_school_staff(self, client):
        """Editing a student requires ``school_staff`` attribute."""
        rel = factories.RelationshipFactory.create(
            from_profile__school_staff=False)
        response = client.get(
            self.url(rel.student), user=rel.elder.user, status=302).follow()

        response.mustcontain("account doesn't have access"), response.html



class TestAddGroup(object):
    """Tests for add_group view."""
    def test_add_group(self, client):
        """User can add a group."""
        teacher = factories.ProfileFactory.create(school_staff=True)
        form = client.get(
            reverse('add_group'), user=teacher.user).forms['add-group-form']
        form['name'] = "Some Group"
        response = form.submit(status=302)

        group = teacher.owned_groups.get()

        assert group.name == "Some Group"
        assert response['Location'] == utils.location(
            reverse('add_student_in_group', kwargs={'group_id': group.id}))


    def test_add_group_with_student(self, client):
        """User can add a group with a student."""
        rel = factories.RelationshipFactory.create(
            from_profile__school_staff=True)
        form = client.get(
            reverse('add_group'), user=rel.elder.user).forms['add-group-form']
        form['name'] = "Some Group"
        form['students'] = [str(rel.student.pk)]
        response = form.submit(status=302)

        group = rel.elder.owned_groups.get()

        assert set(group.students.all()) == {rel.student}
        assert response['Location'] == utils.location(
            reverse('group', kwargs={'group_id': group.id}))


    def test_validation_error(self, client):
        """Name of group must be provided."""
        teacher = factories.ProfileFactory.create(school_staff=True)
        form = client.get(
            reverse('add_group'), user=teacher.user).forms['add-group-form']
        response = form.submit(status=200)

        response.mustcontain("field is required")


    def test_requires_school_staff(self, client):
        """Adding a group requires ``school_staff`` attribute."""
        someone = factories.ProfileFactory.create(school_staff=False)
        response = client.get(
            reverse('add_group'), user=someone.user, status=302).follow()

        response.mustcontain("account doesn't have access"), response.html



class TestEditGroup(object):
    """Tests for edit_group view."""
    def url(self, group=None):
        """Shortcut to get URL of edit-group view."""
        if group is None:
            group = factories.GroupFactory.create()
        return reverse('edit_group', kwargs={'group_id': group.id})


    def test_edit_group(self, client):
        """User can edit a group."""
        group = factories.GroupFactory.create(owner__school_staff=True)
        form = client.get(
            self.url(group),
            user=group.owner.user,
            ).forms['edit-group-form']
        form['name'] = "Some Group"
        response = form.submit(status=302)

        assert response['Location'] == utils.location(
            reverse('group', kwargs={'group_id': group.id}))


    def test_validation_error(self, client):
        """Name of group must be provided."""
        group = factories.GroupFactory.create(
            owner__school_staff=True)
        form = client.get(
            self.url(group),
            user=group.owner.user,
            ).forms['edit-group-form']
        form['name'] = ""
        response = form.submit(status=200)

        response.mustcontain("field is required")


    def test_requires_owner(self, client):
        """Editing a group requires being its owner."""
        group = factories.GroupFactory.create(
            owner__school_staff=True)
        client.get(
            self.url(group),
            user=factories.ProfileFactory.create(school_staff=True).user,
            status=404,
            )



class TestInviteElders(object):
    """Tests for invite_elder view."""
    def url(self, student=None):
        if student is None:
            student = factories.ProfileFactory.create()
        return reverse('invite_elder', kwargs=dict(student_id=student.id))


    def test_invite_elder(self, client):
        """User can invite some elders."""
        rel = factories.RelationshipFactory.create(
            from_profile__school_staff=True)
        response = client.get(self.url(rel.student), user=rel.elder.user)
        form = response.forms['invite-elders-form']
        form['contact'] = "dad@example.com"
        form['relationship'] = "Father"
        form['school_staff'] = False
        response = form.submit(status=302)

        assert response['Location'] == utils.location(
            reverse('village', kwargs={'student_id': rel.student.id}))

        # invite email is sent to new elder
        assert len(mail.outbox) == 1
        assert mail.outbox[0].to == [u'dad@example.com']


    def test_validation_error(self, client):
        """If one elder field is filled out, other must be too."""
        rel = factories.RelationshipFactory.create(
            from_profile__school_staff=True)
        response = client.get(self.url(rel.student), user=rel.elder.user)
        form = response.forms['invite-elders-form']
        form['contact'] = "(123)456-7890"
        form['relationship'] = ""
        form['school_staff'] = False
        response = form.submit(status=200)

        response.mustcontain("field is required")


    def test_requires_school_staff(self, client):
        """Inviting elders requires ``school_staff`` attribute."""
        rel = factories.RelationshipFactory.create(
            from_profile__school_staff=False)
        response = client.get(
            self.url(rel.student), user=rel.elder.user, status=302).follow()

        response.mustcontain("account doesn't have access"), response.html


    def test_requires_relationship(self, client):
        """Only an elder of that student can invite more."""
        elder = factories.ProfileFactory.create(school_staff=True)
        student = factories.ProfileFactory.create()

        client.get(self.url(student), user=elder.user, status=404)



class TestVillage(object):
    """Tests for village chat view."""
    def url(self, student=None):
        if student is None:
            student = factories.ProfileFactory.create()
        return reverse('village', kwargs=dict(student_id=student.id))


    @pytest.mark.parametrize('link_target', ['invite_elder'])
    def test_link_only_if_staff(self, client, link_target):
        """Link with given target is only present for school staff."""
        parent_rel = factories.RelationshipFactory.create(
            from_profile__school_staff=False)
        teacher_rel = factories.RelationshipFactory.create(
            from_profile__school_staff=True, to_profile=parent_rel.student)
        url = self.url(parent_rel.student)
        parent_response = client.get(url, user=parent_rel.elder.user)
        teacher_response = client.get(url, user=teacher_rel.elder.user)
        reverse_kwargs = {}
        if link_target == 'invite_elder':
            reverse_kwargs = {'student_id': parent_rel.student.id}
        target_url = reverse(link_target, kwargs=reverse_kwargs)
        parent_links = parent_response.html.findAll('a', href=target_url)
        teacher_links = teacher_response.html.findAll('a', href=target_url)

        assert len(teacher_links) == 1
        assert len(parent_links) == 0


    def test_requires_relationship(self, client):
        """Only an elder of that student can view village."""
        elder = factories.ProfileFactory.create(school_staff=True)
        student = factories.ProfileFactory.create()

        client.get(self.url(student), user=elder.user, status=404)


    def test_404_deleted_student(self, client):
        """Can't view village of a deleted student."""
        rel = factories.RelationshipFactory.create(
            from_profile__school_staff=True,
            to_profile__deleted=True,
            )

        client.get(self.url(rel.student), user=rel.elder.user, status=404)



class TestAllStudents(object):
    def url(self):
        return reverse('all_students')


    def test_all_students(self, client):
        """Can view an all-students page."""
        teacher = factories.ProfileFactory.create(school_staff=True)
        client.get(self.url(), user=teacher.user, status=200)



class TestGroupDetail(object):
    """Tests for group chat view."""
    def url(self, group=None):
        if group is None:
            group = factories.GroupFactory.create()
        return reverse('group', kwargs=dict(group_id=group.id))


    def test_group_detail(self, client):
        """Can view a group detail page."""
        group = factories.GroupFactory.create(
            owner__school_staff=True)

        client.get(self.url(group), user=group.owner.user, status=200)


    def test_requires_ownership(self, client):
        """Only the owner of a group can view it."""
        group = factories.GroupFactory.create()
        someone = factories.ProfileFactory.create(
            school_staff=True, school=group.owner.school)

        client.get(self.url(group), user=someone.user, status=404)


    def test_404_deleted_group(self, client):
        """Can't view a deleted group."""
        group = factories.GroupFactory.create(
            owner__school_staff=True, deleted=True)

        client.get(self.url(group), user=group.owner.user, status=404)



class TestJsonPosts(object):
    """Tests for json_posts view."""
    def url(self, student=None):
        if student is None:
            student = factories.ProfileFactory.create()
        return reverse('json_posts', kwargs=dict(student_id=student.id))


    def test_requires_relationship(self, client):
        """Only an elder of that student can get posts."""
        elder = factories.ProfileFactory.create(school_staff=True)
        student = factories.ProfileFactory.create()

        client.get(self.url(student), user=elder.user, status=404)


    def test_create_post(self, no_csrf_client):
        """Creates a post and returns its JSON representation."""
        rel = factories.RelationshipFactory.create()

        response = no_csrf_client.post(
            self.url(rel.student), {'text': 'foo'}, user=rel.elder.user)

        assert response.json['success']
        posts = response.json['posts']
        assert len(posts) == 1
        post = posts[0]
        assert post['text'] == 'foo'
        assert post['author_id'] == rel.elder.id
        assert post['student_id'] == rel.student.id


    def test_create_post_with_sequence_id(self, no_csrf_client):
        """Can include a sequence_id with post, will get it back."""
        rel = factories.RelationshipFactory.create()

        response = no_csrf_client.post(
            self.url(rel.student),
            {'text': 'foo', 'author_sequence_id': '5'},
            user=rel.elder.user,
            )

        assert response.json['posts'][0]['author_sequence_id'] == '5'


    def test_length_limit(self, no_csrf_client):
        """Error if post is too long."""
        rel = factories.RelationshipFactory.create(
            from_profile__name='Fred')

        response = no_csrf_client.post(
            self.url(rel.student),
            {'text': 'f' * 160},
            user=rel.elder.user,
            status=400,
            )

        # length limit is 160 - len('Fred: ')
        assert response.json == {
            'success': False,
            'error': "Posts are limited to 153 characters."
            }


    def test_get_posts(self, client):
        """Get backlog posts in chronological order."""
        rel = factories.RelationshipFactory.create(
            from_profile__name='Fred')

        factories.PostFactory(
            timestamp=datetime.datetime(2012, 9, 17, 3, 8, tzinfo=utc),
            author=rel.elder,
            student=rel.student,
            html_text='post1',
            )
        factories.PostFactory(
            timestamp=datetime.datetime(2012, 9, 17, 3, 5, tzinfo=utc),
            author=rel.elder,
            student=rel.student,
            html_text='post2',
            )
        # not in same village, shouldn't be returned
        factories.PostFactory()

        response = client.get(self.url(rel.student), user=rel.elder.user)

        posts = response.json['posts']
        assert [p['text'] for p in posts] == ['post2', 'post1']


    def test_backlog_limit(self, client, monkeypatch):
        """There's a limit on number of posts returned."""
        rel = factories.RelationshipFactory.create(
            from_profile__name='Fred')

        factories.PostFactory(
            timestamp=datetime.datetime(2012, 9, 17, 3, 8, tzinfo=utc),
            author=rel.elder,
            student=rel.student,
            html_text='post1',
            )
        factories.PostFactory(
            timestamp=datetime.datetime(2012, 9, 17, 3, 5, tzinfo=utc),
            author=rel.elder,
            student=rel.student,
            html_text='post2',
            )

        monkeypatch.setattr(views, "BACKLOG_POSTS", 1)
        response = client.get(self.url(rel.student), user=rel.elder.user)

        posts = response.json['posts']
        assert [p['text'] for p in posts] == ['post1']



class TestEditElder(object):
    def url(self, rel=None):
        """rel is relationship between a student and elder to be edited."""
        if rel is None:
            rel = factories.RelationshipFactory()
        return reverse(
            'edit_elder',
            kwargs={'student_id': rel.student.id, 'elder_id': rel.elder.id},
            )


    def test_success(self, client):
        """School staff can edit profile of non school staff."""
        rel = factories.RelationshipFactory(
            from_profile__name='Old Name', from_profile__role='Old Role')
        editor_rel = factories.RelationshipFactory(
            from_profile__school_staff=True, to_profile=rel.to_profile)
        url = self.url(rel)

        form = client.get(
            url, user=editor_rel.elder.user).forms['edit-elder-form']
        form['name'] = 'New Name'
        form['role'] = 'New Role'
        res = form.submit(status=302)

        assert res['Location'] == utils.location(
            reverse('village', kwargs={'student_id': rel.student.id}))
        elder = utils.refresh(rel.elder)
        assert elder.name == 'New Name'
        assert elder.role == 'New Role'


    def test_error(self, client):
        """Test form redisplay with errors."""
        rel = factories.RelationshipFactory()
        editor_rel = factories.RelationshipFactory(
            from_profile__school_staff=True, to_profile=rel.to_profile)
        url = self.url(rel)

        form = client.get(
            url, user=editor_rel.elder.user).forms['edit-elder-form']
        form['name'] = 'New Name'
        form['role'] = ''
        res = form.submit(status=200)

        res.mustcontain('field is required')


    def test_school_staff_required(self, client):
        """Only school staff can access."""
        rel = factories.RelationshipFactory(
            from_profile__name='Old Name', from_profile__role='Old Role')
        editor_rel = factories.RelationshipFactory(
            from_profile__school_staff=False, to_profile=rel.to_profile)
        url = self.url(rel)

        res = client.get(
            url, user=editor_rel.elder.user, status=302).follow()

        res.mustcontain("account doesn't have access")


    def test_cannot_edit_school_staff(self, client):
        """Cannot edit other school staff."""
        rel = factories.RelationshipFactory(
            from_profile__school_staff=True)
        editor_rel = factories.RelationshipFactory(
            from_profile__school_staff=True, to_profile=rel.to_profile)
        url = self.url(rel)

        client.get(url, user=editor_rel.elder.user, status=404)


    def test_requires_relationship(self, client):
        """Editing user must have relationship with student."""
        rel = factories.RelationshipFactory()
        editor = factories.ProfileFactory(school_staff=True)
        url = self.url(rel)

        client.get(url, user=editor.user, status=404)



class TestPdfParentInstructions(object):
    def test_basic(self, client):
        """Smoke test that we get a PDF response back and nothing breaks."""
        elder = factories.ProfileFactory.create(school_staff=True, code='ABCDEF')
        url = reverse('pdf_parent_instructions', kwargs={'lang': 'es'})
        resp = client.get(url, user=elder.user, status=200)

        assert resp.headers[
            'Content-Disposition'] == 'attachment; filename=instructions-es.pdf'
        assert resp.headers['Content-Type'] == 'application/pdf'


    def test_no_code(self, client):
        """Doesn't blow up if requesting user has no code."""
        elder = factories.ProfileFactory.create(school_staff=True)
        url = reverse('pdf_parent_instructions', kwargs={'lang': 'en'})
        resp = client.get(url, user=elder.user, status=200)

        assert resp.headers[
            'Content-Disposition'] == 'attachment; filename=instructions-en.pdf'
        assert resp.headers['Content-Type'] == 'application/pdf'


    def test_missing_template(self, client):
        """404 if template for requested lang is missing."""
        elder = factories.ProfileFactory.create(school_staff=True)
        url = reverse('pdf_parent_instructions', kwargs={'lang': 'en'})
        target = 'portfoliyo.view.village.views.os.path.isfile'
        with mock.patch(target) as mock_isfile:
            mock_isfile.return_value = False
            client.get(url, user=elder.user, status=404)
