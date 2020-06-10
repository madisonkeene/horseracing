# from unittest import TestCase
#
# from horseracing.data_loading import loadRaceInfo, loadAdminConfig
#
# class DataLoadingTest(TestCase):
#     def setUp(self):
#         self.db = sqlite3.connect(":memory:")
#         self.c = self.db.cursor()
#         with open('../horseracing/schema.sql') as f:
#             self.db.executescript(f.read())
#
#     def tearDown(self):
#         self.db.close()
#
#     def test_load_race_info_races(self):
#         loadRaceInfo("test_files/racenight_test.json", self.db)
#
#         got = self.c.execute("SELECT COUNT(*) FROM race;").fetchone()[0]
#         self.assertEqual(got, 2)
#
#         self.assert_single_result("number", "race", "name", "name1")
#         self.assert_single_result("number", "race", "name", "name2")
#
#     def test_load_race_info_horses(self):
#         loadRaceInfo("test_files/racenight_test.json", self.db)
#
#         got = self.c.execute("SELECT COUNT(*) FROM horse;").fetchone()[0]
#         self.assertEqual(got, 4)
#
#         for i in range(1,5):
#             self.assert_single_result("number", "horse", "name", 'horse' + str(i))
#
#     def assert_single_result(self, select_col, table, where_col, where_match):
#         return self.c.execute('SELECT ' + select_col + ' FROM ' + table + ' WHERE ' + where_col + ' = \'' + where_match + '\'').fetchall()
#         self.assertNotEqual(None, got)
#         self.assertEqual(len(got), 1)
#
#     def test_load_admin_config(self):
#         loadAdminConfig("test_files/config.example.json", self.db)
#
#         got = self.c.execute('SELECT id FROM horseracing_admin WHERE username = \'admin\'').fetchall()
#         self.assertNotEqual(None, got)
#         self.assertEqual(len(got), 1)