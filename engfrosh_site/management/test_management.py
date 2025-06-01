from django.test import TestCase
from common_models.models import Team, FroshRole, UserDetails, FacilShift, FacilShiftSignup, \
                                 Calendar, initialize_database, BooleanSetting
from django.contrib.auth.models import Group, User, Permission
from django.urls import reverse


class ManagementTests(TestCase):
    @classmethod
    def setUpClass(self):
        super(ManagementTests, self).setUpClass()
        self.user = User.objects.create_user(username="test", email="test@localhost.com",
                                             password="test", first_name="Test", last_name="McTester")
        self.user.save()

        self.superuser = User.objects.create_user(username="supertest", email="su@localhost.com",
                                                  password="test", is_superuser=True)
        self.superuser.save()

        DEFAULT_ROLES = ("Frosh", "Facil", "Head", "Planning")
        for role in DEFAULT_ROLES:
            if not FroshRole.objects.filter(name=role).exists():
                group = Group(name=role)
                group.save()
                fr = FroshRole(name=role, group=group)
                fr.save()

        self.frosh = Group.objects.get(name="Frosh")
        self.facil = Group.objects.get(name="Facil")
        self.head = Group.objects.get(name="Head")
        self.planning = Group.objects.get(name="Planning")

        self.group1 = Group(name="Team1")
        self.group1.save()
        self.team1 = Team(group=self.group1, display_name="Team1")
        self.team1.save()

        self.group2 = Group(name="Team2")
        self.group2.save()
        self.team2 = Team(group=self.group2, display_name="Team2")
        self.team2.save()

        self.user.groups.add(self.group1)
        self.user.groups.add(self.head)
        self.userdetails = UserDetails(user=self.user, name="Test")
        self.userdetails.save()

        self.frosh1 = User.objects.create_user(username="frosh1", email="frosh1@localhost.com",
                                               password="test", first_name="Frosh", last_name="1")
        self.frosh1.groups.add(self.group1)
        self.frosh1.groups.add(self.frosh)
        self.frosh1.save()
        self.details1 = UserDetails(user=self.frosh1, name="Frosh 1")
        self.details1.save()

        self.frosh2 = User.objects.create_user(username="frosh2", email="frosh2@localhost.com",
                                               password="test", first_name="Frosh", last_name="2")
        self.frosh2.groups.add(self.group2)
        self.frosh2.groups.add(self.frosh)
        self.frosh2.save()
        self.details2 = UserDetails(user=self.frosh2, name="Frosh 2")
        self.details2.save()

        self.cal1 = Calendar(name="test", slug="test")
        self.cal1.save()
        self.cal2 = Calendar(name="Planning", slug="plan")
        self.cal2.save()

        self.shift1 = FacilShift(name="Test1", desc="a", flags="a", type="wt",
                                 max_facils=0, administrative=False, checkin_user=self.superuser)
        self.shift1.save()
        self.signup1 = FacilShiftSignup(shift=self.shift1, user=self.frosh1)
        self.signup1.save()
        self.signup2 = FacilShiftSignup(shift=self.shift1, user=self.user)
        self.signup2.save()

        self.shift2 = FacilShift(name="Test2", desc="a", flags="a",
                                 max_facils=0, administrative=True, checkin_user=self.user)
        self.shift2.save()
        self.signup3 = FacilShiftSignup(shift=self.shift2, user=self.frosh2)
        self.signup3.save()

        initialize_database()

    def test_frosh_list(self):
        # Test perms
        frosh_list_perm = Permission.objects.get(codename='frosh_list')
        self.user.user_permissions.remove(frosh_list_perm)
        self.user.save()
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("frosh_list"))
        self.assertEqual(response.status_code, 302)
        self.user.user_permissions.add(frosh_list_perm)
        self.user.save()

        # Test search
        response = self.client.get(reverse("frosh_list"))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse("frosh_list") + "?name=Frosh")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertTrue("Frosh 1" in content)
        self.assertTrue("Frosh 2" in content)
        response = self.client.get(reverse("frosh_list") + "?name=Frosh%201")
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertTrue("Frosh 1" in content)
        self.assertTrue("Frosh 2" not in content)

    def test_generate_bus(self):
        # Test perms
        response = self.client.get(reverse("gen_bus"))
        self.assertEqual(response.status_code, 302)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("gen_bus"))
        self.assertEqual(response.status_code, 302)

        # Test shift creation
        self.client.login(username="supertest", password="test")
        response = self.client.get(reverse("gen_bus"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(FacilShift.objects.all()), 4)
        self.assertEqual(len(FacilShiftSignup.objects
                                             .filter(shift=FacilShift.objects
                                                                     .get(name="Team1-BusMorning"))), 2)
        self.assertEqual(len(FacilShiftSignup.objects
                                             .filter(shift=FacilShift.objects
                                                                     .get(name="Team2-BusMorning"))), 1)

    def test_shift_checkin(self):
        # Test perms
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("shift_checkin", args=[1]))
        self.assertEqual(response.status_code, 302)

        # Test shift retrieval
        perm = Permission.objects.get(codename='attendance_manage')
        self.user.user_permissions.add(perm)
        self.user.save()

        # Test with no shift specified
        response = self.client.get(reverse("shift_checkin", args=[1000]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), "Invalid shift!")

        # Test with shift with a wrong designated checkin user
        response = self.client.get(reverse("shift_checkin", args=[self.shift1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), "You are not authorized to check in this shift!")

        # Test with shift with the correct checkin user
        self.shift1.checkin_user = self.user
        self.shift1.save()
        response = self.client.get(reverse("shift_checkin", args=[self.shift1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.decode('utf-8'), "You are not authorized to check in this shift!")

        # Test returning users for shift
        response = self.client.get(reverse("shift_checkin", args=[self.shift1.id]))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertTrue("Frosh" in content)
        self.assertTrue("McTester" in content)

        # Test setting attendance for WT with incomplete WT waiver
        response = self.client.post(reverse("shift_checkin", args=[self.shift1.id]),
                                    {"signup": self.signup1.id, "action": "attendance", "switch": "True"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode('utf-8'), "Incomplete waiver!")
        self.assertFalse(UserDetails.objects.get(user=self.frosh1).wt_waiver_completed)

        # Test completing waiver and setting attendance for WT
        response = self.client.post(reverse("shift_checkin", args=[self.shift1.id]),
                                    {"signup": self.signup1.id, "action": "wt_waiver"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(UserDetails.objects.get(user=self.frosh1).wt_waiver_completed)
        response = self.client.post(reverse("shift_checkin", args=[self.shift1.id]),
                                    {"signup": self.signup1.id, "action": "attendance", "switch": "True"})
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.content.decode('utf-8'), "Incomplete waiver!")
        self.assertTrue(FacilShiftSignup.objects.get(id=self.signup1.id).attendance)

        # Test setting attendance for non WT
        response = self.client.post(reverse("shift_checkin", args=[self.shift2.id]),
                                    {"signup": self.signup3.id, "action": "attendance", "switch": "True"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(FacilShiftSignup.objects.get(id=self.signup3.id).attendance)

        # Test setting attendance to false for non WT
        response = self.client.post(reverse("shift_checkin", args=[self.shift2.id]),
                                    {"signup": self.signup3.id, "action": "attendance", "switch": "False"})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(FacilShiftSignup.objects.get(id=self.signup3.id).attendance)

    def test_show_calendars(self):
        # Test perms
        perm = Permission.objects.get(codename='calendar_manage')
        self.user.user_permissions.remove(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("show_calendars"))
        self.assertEqual(response.status_code, 302)

        # Test show calendars
        self.user.user_permissions.add(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("show_calendars"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode('utf-8')
        self.assertFalse("test" in content)
        self.assertTrue("Planning" in content)

    def test_edit_calendar(self):
        # Test perms
        perm = Permission.objects.get(codename='calendar_manage')
        self.user.user_permissions.remove(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("edit_calendar", args=[1000]))
        self.assertEqual(response.status_code, 302)

        # Test edit with no id
        self.user.user_permissions.add(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("edit_calendar", args=[0]))
        self.assertEqual(response.status_code, 200)

        # Test edit GET with id
        response = self.client.get(reverse("edit_calendar", args=[self.cal1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("test" in response.content.decode('utf-8'))

        # Test edit POST with id
        response = self.client.post(reverse("edit_calendar", args=[self.cal1.id]),
                                    {"name": "test", "slug": ""})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Calendar.objects.get(id=self.cal1.id).slug, "test")

        response = self.client.post(reverse("edit_calendar", args=[self.cal1.id]),
                                    {"name": "test", "slug": "test2"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Calendar.objects.get(id=self.cal1.id).slug, "test2")

    def test_lock_scav(self):
        # Test perms
        perm = Permission.objects.get(codename='lock_scav')
        self.user.user_permissions.remove(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("lock_scav"))
        self.assertEqual(response.status_code, 302)

        # Set defaults
        scav = BooleanSetting.objects.get(id="SCAVENGER_ENABLED")
        scav.value = False
        scav.save()
        tradeup = BooleanSetting.objects.get(id="TRADE_UP_ENABLED")
        tradeup.value = False
        tradeup.save()

        # Test lock GET
        self.user.user_permissions.add(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("lock_scav"))
        self.assertEqual(response.status_code, 200)

        # Test lock POST
        response = self.client.post(reverse("lock_scav"))
        self.assertEqual(response.status_code, 200)
        scav = BooleanSetting.objects.get(id="SCAVENGER_ENABLED")
        self.assertTrue(scav.value)
        tradeup = BooleanSetting.objects.get(id="TRADE_UP_ENABLED")
        self.assertTrue(tradeup.value)

        # Test unlock POST
        response = self.client.post(reverse("lock_scav"))
        self.assertEqual(response.status_code, 200)
        scav = BooleanSetting.objects.get(id="SCAVENGER_ENABLED")
        self.assertFalse(scav.value)
        tradeup = BooleanSetting.objects.get(id="TRADE_UP_ENABLED")
        self.assertFalse(tradeup.value)

    def test_shift_edit(self):
        # Test perms
        perm = Permission.objects.get(codename='shift_manage')
        self.user.user_permissions.remove(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("shift_edit", args=[1000]))
        self.assertEqual(response.status_code, 302)

        # Test GET
        self.user.user_permissions.add(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("shift_edit", args=[self.shift1.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Test1" in response.content.decode('utf-8'))

        response = self.client.get(reverse("shift_edit", args=[0]))
        self.assertEqual(response.status_code, 200)
        self.assertFalse("Test1" in response.content.decode('utf-8'))

        # Test POST
        data = {"name": "Test5", "desc": "a", "flags": "a", "start": "",
                "end": "", "max_facils": 0, "administrative": False, "checkin_user": "", "type": ""}

        response = self.client.post(reverse("shift_edit", args=[self.shift1.id]), data)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("Test5" in response.content.decode('utf-8'))
        self.shift1 = FacilShift.objects.get(id=self.shift1.id)
        self.assertEqual(self.shift1.name, "Test5")
        self.assertEqual(self.shift1.desc, "a")
        self.assertEqual(self.shift1.flags, "a")
        self.assertEqual(self.shift1.start, None)
        self.assertEqual(self.shift1.end, None)
        self.assertEqual(self.shift1.max_facils, 0)
        self.assertFalse(self.shift1.administrative)
        self.assertEqual(self.shift1.checkin_user, None)
        self.assertEqual(self.shift1.type, "")

        # Reset
        data['name'] = "Test1"
        response = self.client.post(reverse("shift_edit", args=[self.shift1.id]), data)
        self.shift1 = FacilShift.objects.get(id=self.shift1.id)
        self.assertEqual(response.status_code, 200)

    def test_facil_shifts(self):
        # Test perms
        perm = Permission.objects.get(codename='facil_signup')
        self.user.user_permissions.remove(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("facil_shifts"))
        self.assertEqual(response.status_code, 302)

        # Test GET
        self.user.user_permissions.add(perm)
        self.client.login(username="test", password="test")
        response = self.client.get(reverse("facil_shifts"))
        # TODO: Implement rest of this test and the ones after it
