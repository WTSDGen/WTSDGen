import unittest
import os
import shutil

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from scripts.housekeeping.datadir import get_save_dir
from scripts.game_structure.game_essentials import Game

if not os.path.exists('tests/testSaves'):
    num_example_saves = 0
else:
    _tmp = os.listdir('tests/testSaves')
    num_example_saves = 0
    for i in _tmp:
        if i.startswith('save'):
            num_example_saves += 1


@unittest.skipIf(num_example_saves == 0, "No example saves found. Download the contents of https://github.com/ImLvna/warrengen-unittest-saves into tests/testSaves to run unittest")
class LoadSave(unittest.TestCase):

    def setUp(self):
        if os.path.exists(get_save_dir()):
            shutil.move(get_save_dir(), 'saves_backup')

    def tearDown(self):
        if os.path.exists(get_save_dir()):
            shutil.rmtree(get_save_dir())
        if os.path.exists('saves_backup'):
            shutil.move('saves_backup', get_save_dir())

    def old_implimentation(self):
        with open(get_save_dir() + '/warrenlist.txt', 'r') as read_file:
            warren_list = read_file.read()
            if_warrens = len(warren_list)
        if if_warrens > 0:
            warren_list = warren_list.split('\n')
            warren_list = [i.strip() for i in warren_list if i]  # Remove empty and whitespace
            return warren_list
        else:
            return None
        
    def new_implimentation(self):
        return Game().read_warrens()
    
    def example_save(self, id):
        if os.path.exists(get_save_dir()):
            shutil.rmtree(get_save_dir())

        #copy tests/testSaves/save<id> to saves
        shutil.copytree('tests/testSaves/save' + str(id), get_save_dir())
    

    def test_check_current_warren(self):
        for i in range(1, num_example_saves + 1):
            with self.subTest(i=i):
                print("Checking current Warren for save " + str(i))
                self.example_save(i)
                fileList = os.listdir(get_save_dir())
                if 'currentwarren.txt' in fileList:
                    self.skipTest("Save " + str(i) + " already migrated")
                old_out = self.old_implimentation()
                self.example_save(i)
                new_out = self.new_implimentation()
                

                self.assertEqual(old_out[0], new_out[0], "Current Warren not saved correctly for save " + str(i))
    
    
    
    def test_check_warren_list(self):

        for i in range(1, num_example_saves + 1):
            with self.subTest(i=i):
                print("Checking warren list for save " + str(i))
                self.example_save(i)
                fileList = os.listdir(get_save_dir())
                if 'currentwarren.txt' in fileList:
                    self.skipTest("Save " + str(i) + " already migrated")
                old_out = self.old_implimentation().sort()
                self.example_save(i)
                new_out = self.new_implimentation().sort()

                self.assertEqual(old_out, new_out, "Warren list not saved correctly for save " + str(i))

@unittest.skipIf(num_example_saves == 0, "No example saves found. Download the contents of https://github.com/ImLvna/warrengen-unittest-saves into tests/testSaves to run unittest")
class MigrateSave(unittest.TestCase):
    def setUp(self):
        if os.path.exists(get_save_dir()):
            shutil.move(get_save_dir(), 'saves_backup')

    def tearDown(self):
        if os.path.exists(get_save_dir()):
            shutil.rmtree(get_save_dir())
        if os.path.exists('saves_backup'):
            shutil.move('saves_backup', get_save_dir())

    def example_save(self, id):
        if os.path.exists(get_save_dir()):
            shutil.rmtree(get_save_dir())

        #copy tests/testSaves/save<id> to saves
        shutil.copytree('tests/testSaves/save' + str(id), get_save_dir())

    def test_migrate_save_onread(self):
        
        for i in range(1, num_example_saves + 1):
            with self.subTest(i=i):
                print("Checking migration for save " + str(i))
                self.example_save(i)
                fileList = os.listdir(get_save_dir())
                if 'currentwarren.txt' in fileList:
                    self.skipTest("Save " + str(i) + " already migrated")
                
                with open(get_save_dir() + '/warrenlist.txt', 'r') as read_file:
                    warren_name = read_file.read().strip().splitlines()[0]

                Game().read_warrens() # the load save function should migrate the save

                fileList = os.listdir(get_save_dir())
                self.assertIn('currentwarren.txt', fileList, "Save " + str(i) + " not migrated")

                with open(get_save_dir() + '/currentwarren.txt', 'r') as read_file:
                    curwarren = read_file.read().strip()

                self.assertEqual(curwarren, warren_name, "Save " + str(i) + " not migrated correctly")
                self.assertNotIn('warrenlist.txt', fileList, "Save " + str(i) + " not migrated correctly")
