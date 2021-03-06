import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame
import time
import math
import numpy as np
import random
import copy
from fd import Fast_Downward

# np.random.seed(437)
pygame.init()
pygame.display.set_caption("Grocery Packing")


class Grocery_item:
    def __init__(self, x, y, image_path,image_width,image_height,
                object_name,cx):
        self.x = x
        self.y = y
        self.cx = cx
        self.cy= 480-image_height
        self.width = image_width
        self.height = image_height
        self.body = pygame.image.load(image_path)
        self.item_at_left = None
        self.item_at_right = None
        self.item_on_top = None
        self.item_on_bottom = None
        self.on_table = False
        self.on_clutter_or_table = False
        self.onsomething = False
        self.being_held = False
        self.name = object_name
        self.holding = None #only for gripper



    def move_to(self, x, y):
        self.x = x
        self.y = y



class environment:
    def __init__(self, uncertain="low", declutter=False, order=0):
        self.table = Grocery_item(150,300,'assets/table.jpg',419,144,"table",0)
        self.pepsi = Grocery_item(10, 400,'assets/pepsi.jpg',26,49,"pepsi",200)
        self.nutella = Grocery_item(15, 400,'assets/nutella.jpg',26,37,"nutella",250)
        self.coke = Grocery_item(20, 400, 'assets/coke.jpg',28,52,"coke",300)
        self.lipton = Grocery_item(25, 400, 'assets/lipton.jpg',58,28,"lipton",350)
        self.bleach = Grocery_item(13, 400, 'assets/bleach.jpg',26,64,"bleach",400)
        self.gripper = Grocery_item(350, 0,'assets/gripper.png',75,75,"gripper",0)
        self.logo = Grocery_item(0,0, 'assets/4progress.png',535,78,"logo",0)
        self.perceived = None

        self.uncertainty = uncertain 
        self.declutter = declutter
        self.init_order = order
        self.domain_path='/home/developer/uncertainty/pddl/dom.pddl'
        self.problem_path='/home/developer/uncertainty/pddl/prob.pddl'
        self.definition = "(define (problem PACKED-GROCERY) \n (:domain GROCERY) \
                            \n (:objects bleach nutella coke pepsi lipton - item) \n"
        self.goal_def = "\n(:goal (and (on pepsi bleach) (on lipton pepsi) (toleft coke bleach) (toright nutella bleach))))\n"


        self.items = {"pepsi":self.pepsi, "nutella":self.nutella,
                      "coke": self.coke, "lipton": self.lipton,
                      "bleach": self.bleach, "table":self.table}
        self.objects_list = [self.pepsi, self.nutella,self.coke,self.lipton,
                    self.bleach]
        self.clock = pygame.time.Clock()
        self.current_action = "Action: (pick-up-from-on nutella bleach)"
        self.certainty_level = "Uncertainty Level: "+uncertain
        self.clutter_strategy = "Clutter Strategy: Declutter first" if declutter else "Clutter Strategy: Optimistic"
        self.start_time = time.time()
        self.win = pygame.display.set_mode((700,480))
        self.rate = 120


    def run(self):
        if self.declutter:
            self.declutter_before_clutter_planning()
        else:
            self.clutter_optimistic_planning()

    def sample_object(self, object_name):
        if self.uncertainty == "low":
            return self.items[object_name]
        # print("UNCERTAIN")
        mid_item_probabilities = {
             "pepsi":[0.4, 0.1,0.3,0.1,0.1],
              "nutella":[0.2,0.4,0.2,0.1,0.1],
              "coke":[0.3,0.2,0.4,0.05,0.05],
              "lipton":[0.2,0.1,0.1,0.4,0.2],
              "bleach":[0.1,0.1,0.1,0.1,0.6]

            }
        high_item_probabilities = {
             "pepsi":[0.25, 0.2,0.2,0.2,0.15],
              "nutella":[0.2,0.25,0.2,0.2,0.15],
              "coke":[0.2,0.2,0.25,0.15,0.2],
              "lipton":[0.2,0.15,0.2,0.25,0.2],
              "bleach":[0.2,0.2,0.2,0.15,0.25]

            }
        probabilities = mid_item_probabilities if self.uncertainty=="medium" else high_item_probabilities

        choice = np.random.choice(self.objects_list, size=1, 
                p=probabilities[object_name])

        decision = choice[0]

        count = 0
        while decision.onsomething:
            # print("not choosing "+choice[0].name+". Choosing from clutter")
            choice = np.random.choice(self.objects_list, size=1, 
                p=probabilities[object_name])
            count+=1
            if count > 20:
                return self.items[object_name]


        return decision


    def initialize_clutter(self):
        # choice = 0#np.random.randint(4)
        choice = self.init_order

        if choice == 0:
            self.bleach.item_at_left = "lipton"
            self.lipton.item_at_right = "bleach"
            self.bleach.item_on_top = "pepsi"
            self.pepsi.onsomething = True
            self.bleach.item_at_right = "coke"
            self.coke.item_at_left = "bleach"
            self.coke.item_on_top = "nutella"
            self.nutella.onsomething = True
            self.pepsi.item_at_right = "nutella"
            self.nutella.item_at_left = "coke"
            self.lipton.on_clutter_or_table = True
            self.bleach.on_clutter_or_table = True
            self.coke.on_clutter_or_table = True

        elif choice == 1:
            self.lipton.item_at_left = "coke"
            self.coke.item_at_right = "lipton"
            self.lipton.item_on_top = "nutella"
            self.nutella.onsomething = True
            self.lipton.item_at_right = "bleach"
            self.bleach.item_at_left = "lipton"
            self.bleach.item_at_right = "pepsi"
            self.pepsi.item_at_left = "bleach"
            self.coke.on_clutter_or_table = True
            self.lipton.on_clutter_or_table = True
            self.bleach.on_clutter_or_table = True
            self.pepsi.on_clutter_or_table = True

        elif choice == 2:
            self.lipton.item_at_left = "nutella"
            self.nutella.item_at_right = "lipton"

            self.lipton.item_at_right = "pepsi"
            self.pepsi.item_at_left = "lipton"

            self.lipton.item_on_top = "coke"
            self.coke.onsomething = True
            self.coke.item_on_top = "bleach"
            self.bleach.onsomething  =True

            self.nutella.on_clutter_or_table = True
            self.lipton.on_clutter_or_table = True 
            self.pepsi.on_clutter_or_table = True

        elif choice == 3:
            self.lipton.item_on_top = "pepsi"
            self.pepsi.onsomething = True

            self.lipton.item_at_right = "coke"
            self.coke.item_at_left = "lipton"

            self.coke.item_on_top = "bleach"
            self.bleach.onsomething = True

            self.coke.item_at_right = "nutella"
            self.nutella.item_at_left = "coke"

            self.lipton.on_clutter_or_table = True
            self.coke.on_clutter_or_table = True
            self.nutella.on_clutter_or_table = True

        self.draw_init_clutter(choice)


    def draw_init_clutter(self, choice):
        if choice == 0:
            self.lipton.x = 10
            self.lipton.y = 480-self.lipton.height
            self.bleach.x = 10+self.lipton.width
            self.bleach.y = 480-self.bleach.height
            self.coke.x = 10+self.lipton.width+self.bleach.width
            self.coke.y = 480-self.coke.height
            self.pepsi.x = 10+self.lipton.width
            self.pepsi.y = 480-self.bleach.height-self.pepsi.height
            self.nutella.x = 10+self.lipton.width+self.bleach.width
            self.nutella.y = 480 - self.coke.height-self.nutella.height

        elif choice ==1:
            self.coke.x = 10
            self.lipton.x = 10+self.coke.width 
            self.bleach.x = 10+self.coke.width+self.lipton.width
            self.pepsi.x = 10+self.coke.width+self.lipton.width+self.bleach.width
            self.nutella.x = 10+self.coke.width 

            self.coke.y = 480-self.coke.height 
            self.lipton.y = 480-self.lipton.height 
            self.bleach.y = 480-self.bleach.height 
            self.pepsi.y = 480-self.pepsi.height 
            self.nutella.y = 480-self.lipton.height-self.nutella.height

        elif choice == 2:
            self.nutella.x = 10
            self.lipton.x = 10+self.nutella.width 
            self.pepsi.x = 10+self.nutella.width +self.lipton.width
            self.coke.x = 10+self.nutella.width
            self.bleach.x = 10+self.nutella.width

            self.nutella.y = 480-self.nutella.height 
            self.lipton.y = 480-self.lipton.height
            self.pepsi.y = 480-self.pepsi.height 
            self.coke.y = 480-self.lipton.height-self.coke.height 
            self.bleach.y = 480-self.lipton.height-self.coke.height-self.bleach.height

        elif choice == 3:
            self.lipton.x = 10
            self.coke.x = 10+self.lipton.width
            self.nutella.x = 10+self.lipton.width+self.coke.width 
            self.pepsi.x = 10
            self.bleach.x = 10+self.lipton.width

            self.lipton.y = 480 - self.lipton.height
            self.coke.y = 480-self.coke.height
            self.nutella.y = 480-self.nutella.height 
            self.pepsi.y = 480 - self.lipton.height-self.pepsi.height 
            self.bleach.y = 480-self.coke.height - self.bleach.height


    def display_text(self,textcontent,w):
        font = pygame.font.Font('freesansbold.ttf',14)
        text = font.render(textcontent, True, (0,0,0))
        self.win.blit(text, (410,200+w))



    def redrawGameWindow(self):
        self.win.fill((255,255,255))
        self.win.blit(pygame.image.load('assets/box.jpg'), (280,160))
        self.win.blit(pygame.image.load('assets/box.jpg'), (390,160))
        self.win.blit(pygame.image.load('assets/box_lat.jpg'), (290,290))
        self.win.blit(self.logo.body, (self.logo.x, self.logo.y))
        self.win.blit(pygame.image.load('assets/rt.jpg'), (550,10))
        self.win.blit(self.table.body,(self.table.x, self.table.y))
        self.win.blit(self.pepsi.body,(self.pepsi.x, self.pepsi.y))
        self.win.blit(self.nutella.body,(self.nutella.x, self.nutella.y))
        self.win.blit(self.coke.body,(self.coke.x, self.coke.y))
        self.win.blit(self.lipton.body,(self.lipton.x, self.lipton.y))
        self.win.blit(self.bleach.body,(self.bleach.x, self.bleach.y))
        self.win.blit(self.gripper.body,(self.gripper.x, self.gripper.y))
        self.display_text(self.current_action,0)
        self.duration = int(time.time()-self.start_time)
        self.duration_in_sec = "Duration: "+str(self.duration)+ " seconds"
        self.display_text(self.duration_in_sec, 20)
        self.display_text("Uncertainty Level: "+self.uncertainty, 40)
        self.display_text(self.clutter_strategy, 60)

        if self.perceived is not None:
            self.win.blit(pygame.transform.scale(self.perceived.body,(15,30)),(585,20))        
        
        
        pygame.display.update()

    def execute_action(self, action):
        if action[0] == 'pick-up':
            self.pick_up(action[1])
        elif action[0] == 'pick-up-from-on':
            self.pick_up(action[1])
        elif action[0] == 'put-on-table':
            self.put_on_table(action[1])
        elif action[0] == 'put-on':
            self.put_on(action[1], action[2])
        elif action[0] == 'put-left':
            self.put_left(action[1],action[2])
        elif action[0] == 'put-right':
            self.put_right(action[1], action[2])
        elif action[0] == 'drop-in-clutter':
            self.drop_in_clutter(action[1])


    def inspect_scene(self, action):
        result = True
        # for action in progress:
        if action[0] == 'put-on-table':
            result = result and self.check_on_table(action[1])
            if not result:
                print("ERROR in put-on-table")
        elif action[0] == 'put-on':
            result = result and self.check_on(action[1],action[2])
            if not result:
                print("ERROR in put-on")
        elif action[0] == 'put-left':
            result = result and self.check_left(action[1],action[2])
            if not result:
                print("ERROR in put-left")
        elif action[0] == 'put-right':
            result = result and self.check_right(action[1],action[2])
            if not result:
                print("ERROR in put-right")
        elif action[0] == 'pick-up':
            result = result and (self.gripper.holding == action[1])
            if not result:
                print("ERROR in holding")
        elif action[0] == 'pick-up-from-on':
            result = result and (self.gripper.holding == action[1])
            if not result:
                print("ERROR in pick-up-from")
        return result


    def check_on_table(self, item_name):
        item = self.items[item_name]
        return item.on_table
        # if item.y == 260:
        #     return True
        # else:
        #     return False


    def check_left(self, left_item_name, right_item_name):
        left_item = self.items[left_item_name]
        right_item = self.items[right_item_name]

        return (right_item.item_at_left == left_item_name)
        # if (right_item.x - left_item.x) == 50:
        #     return True
        # else:
        #     return False


    def check_right(self, left_item_name, right_item_name):
        left_item = self.items[left_item_name]
        right_item = self.items[right_item_name]

        return (right_item.item_at_right == left_item_name)

        # if (left_item.x - right_item.x) == 50:
        #     return True
        # else:
        #     return False


    def check_on(self, top_item_name, bot_item_name):
        top_item = self.items[top_item_name]
        bot_item = self.items[bot_item_name]

        return (bot_item.item_on_top == top_item_name)

        # if (bot_item.y - top_item.y) == 64:
        #     return True
        # else:
        #     return False


    def get_current_packing_state(self):
        init = "\n(:init "
        for item in self.objects_list:
            if item.item_at_left == None:
                init+=" (clearleft "+item.name+")"
            else:
                init+=" (toleft "+item.item_at_left+" "+ item.name+")"

            if item.item_at_right == None:
                init+=" (clearright "+item.name+")"
            else:
                init+=" (toright "+item.item_at_right+" "+item.name+")"

            
            if item.item_on_top == None:
                init+=" (cleartop "+item.name+")"
            else:
                init+=" (on "+item.item_on_top+" "+item.name+")"

            if item.on_table:
                init+=" (ontable "+item.name+")"

            if item.on_clutter_or_table:
                init+=" (onclutterortable "+item.name+")"


            if item.onsomething:
                init+=" (onsomething "+item.name+")"

        if self.gripper.holding == None:
            init+=" (handempty) "
        else:
            init+=" (holding "+self.gripper.holding+") "
        init+=")\n"
        return init


    def form_problem_from_current_scene(self):
        init = self.get_current_packing_state()
        prob = self.definition+init+self.goal_def
        f = open("newprob.pddl","w")
        f.write(prob)
        f.close()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        prob_path = dir_path+"/"+"newprob.pddl"
        
        return prob_path

    def form_dec_problem_from_current_scene(self):
        init = self.get_current_packing_state()
        goal = "\n(:goal (and (cleartop coke) \
        (cleartop lipton) (cleartop nutella) \
        (cleartop pepsi) (cleartop bleach))))"
        prob = self.definition+init+goal
        f = open("newprob.pddl","w")
        f.write(prob)
        f.close()
        dir_path = os.path.dirname(os.path.realpath(__file__))
        prob_path = dir_path+"/"+"newprob.pddl"
        
        return prob_path


    def clutter_optimistic_planning(self):
        start_time = time.time()
        self.initialize_clutter()
        problem = self.form_problem_from_current_scene()
        self.run_grocery_packing(self.domain_path, problem) 
        duration = time.time() - start_time
        print("\n\n DURATION OF OPTIMISTIC IS "+str(duration)+" seconds")
        time.sleep(3)
        pygame.quit()


    def declutter_before_clutter_planning(self):
        start_time = time.time()
        self.initialize_clutter()
        init = self.get_current_packing_state()
        goal = "\n(:goal (and (cleartop coke) \
        (cleartop lipton) (cleartop nutella) \
        (cleartop pepsi) (cleartop bleach))))"
        problem = self.definition+init+goal
        file = open("declutterprob.pddl",'w')
        file.write(problem)
        file.close()
        clutter_prob_path = os.path.dirname(os.path.realpath(__file__))+\
                    "/"+"declutterprob.pddl" 
        uncert = copy.deepcopy(self.uncertainty)
        self.uncertainty = 'low'
        self.run_dec_grocery_packing(self.domain_path, clutter_prob_path)
        print("***Declutter Complete***")
        self.uncertainty = uncert


        inits = self.get_current_packing_state()
        problems = self.definition+inits+self.goal_def
        file = open("probs.pddl",'w')
        file.write(problems)
        file.close()
        probs_path = os.path.dirname(os.path.realpath(__file__))+\
                    "/"+"probs.pddl"
        self.run_grocery_packing(self.domain_path, probs_path)
        print("***GROCERY PACKING COMPLETE***")
        duration = time.time() - start_time
        print("\n\nDURATION OF DECLUTTER IS "+str(duration)+" seconds")
        pygame.quit()

        

    def run_grocery_packing(self,domain_path, problem_path):
        # action_progress=[] 
        f = Fast_Downward()
        plan = f.plan(domain_path, problem_path)
        # print(plan)
        if plan is None or len(plan)==0:
            print('No valid plan found')
            return
        else:
            for action in plan:
                self.redrawGameWindow()               
                print('Performing action: '+str(action))
                self.current_action = "Action: "+str(action)
                self.execute_action(action)
                inspection_result = self.inspect_scene(action)
                if not inspection_result:
                    self.current_action = "Action: REPLANNING..."
                    self.redrawGameWindow()
                    print('****************')
                    print('REPLANNING...')
                    print('****************')
                    time.sleep(3)
                    prob_path = self.form_problem_from_current_scene()
                    self.run_grocery_packing(domain_path, prob_path)
            # return


        
        time.sleep(2)

    def run_dec_grocery_packing(self,domain_path, problem_path):
        # action_progress=[] 
        f = Fast_Downward()
        plan = f.plan(domain_path, problem_path)
        # print(plan)
        if plan is None or len(plan)==0:
            print('No valid plan found')
            return
        else:
            for action in plan:
                self.redrawGameWindow()               
                print('Performing action: '+str(action))
                self.current_action = "Action: "+str(action)
                self.execute_action(action)
                inspection_result = self.inspect_scene(action)
                if not inspection_result:
                    self.current_action = "Action: REPLANNING..."
                    self.redrawGameWindow()
                    print('****************')
                    print('REPLANNING...')
                    print('****************')
                    time.sleep(3)
                    prob_path = self.form_dec_problem_from_current_scene()
                    self.run_dec_grocery_packing(domain_path, prob_path)


    def pick_motion(self, item):
        orig_x = self.gripper.x
        orig_y = self.gripper.y 
        while math.fabs(item.x - (self.gripper.x+26)) > 0:
            if item.x - (self.gripper.x+26) > 0:
                self.gripper.x += 1
            elif item.x - (self.gripper.x+26) < 0:
                self.gripper.x -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)
        # print('done moving left')

        while math.fabs(item.y - (self.gripper.y+90)) > 0:
            if item.y - (self.gripper.y+90) > 0:
                self.gripper.y += 1
            elif item.y - (self.gripper.y+90) < 0:
                self.gripper.y -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)

        # print('done moving right')
        # time.sleep(2)
        # print('moving back')
        while math.fabs(orig_y - self.gripper.y) > 0:
            if (orig_y - self.gripper.y) > 0:
                self.gripper.y += 1
                item.y += 1
            elif (orig_y - self.gripper.y) < 0:
                self.gripper.y -= 1
                item.y -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)


        while math.fabs(orig_x - self.gripper.x) > 0:
            if (orig_x - self.gripper.x) > 0:
                self.gripper.x += 1
                item.x += 1
            elif (orig_y - self.gripper.x) < 0:
                self.gripper.x -= 1
                item.x -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)


    def pick_up(self, item):
        fp = np.random.randint(20)
        if fp == 10:  #5% probability of false positive localization
            self.missed_pick()
            return

        s_item = self.sample_object(item)
        self.perceived = s_item
        # print("picking "+s_item.name)
        if not (s_item.item_on_top == None):
            print("won't pick "+s_item.name)
            return
        
        

        s_item.item_on_bottom=None
        s_item.item_on_top=None
        s_item.item_at_left=None
        s_item.item_at_right=None
        s_item.on_table=False
        s_item.onsomething=False
        s_item.on_clutter_or_table=False
        s_item.being_held = True

        item = s_item.name

        for it in self.objects_list:
            if it.item_on_top == item:
                it.item_on_top = None
            elif it.item_on_bottom == item:
                it.item_on_bottom = None
            elif it.item_at_right == item:
                it.item_at_right = None
            elif it.item_at_left == item:
                it.item_at_left = None
        self.gripper.holding = s_item.name
        self.pick_motion(s_item)


        #put top on botton
    def put_on(self, topitem, bottomitem):
        if topitem == bottomitem:
            return
        top = self.items[topitem]
        bot = self.items[bottomitem]
        if (not bot.onsomething) and (bot.item_on_bottom == None) :
            return
        self.gripper.holding = None
        bot.item_on_top = topitem

        orig_x = self.gripper.x
        orig_y = self.gripper.y
        while math.fabs(top.x - bot.x) > 0:
            if (top.x - bot.x) > 0:
                top.x-=1
                self.gripper.x -=1

            elif (top.x - bot.x) < 0:
                top.x += 1
                self.gripper.x +=1
            
            self.redrawGameWindow()
            self.clock.tick(self.rate)

        ymargin = top.y + top.height
        while math.fabs(top.y + top.height - bot.y) > 0:
            if (top.y + top.height - bot.y) > 0:
                top.y-=1
                self.gripper.y -=1

            elif (top.y + top.height - bot.y) < 0:
                top.y += 1
                self.gripper.y +=1
            
            self.redrawGameWindow()
            self.clock.tick(self.rate)

        # print('moving back')
        while math.fabs(orig_y - self.gripper.y) > 0:
            if (orig_y - self.gripper.y) > 0:
                self.gripper.y += 1
            elif (orig_y - self.gripper.y) < 0:
                self.gripper.y -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)


        while math.fabs(orig_x - self.gripper.x) > 0:
            if (orig_x - self.gripper.x) > 0:
                self.gripper.x += 1
            elif (orig_y - self.gripper.x) < 0:
                self.gripper.x -= 1
            self.redrawGameWindow()
            self.clock.tick(self.rate)
        top.item_on_bottom = bot.name
        top.onsomething=True


    def put_on_table(self, topitem):
        top = self.items[topitem]
        if not (self.gripper.holding == topitem):
            return
        self.gripper.holding = None
        top.on_table = True
        top.onsomething=True

        bot = self.items['table']
        orig_x = self.gripper.x
        orig_y = self.gripper.y
        while math.fabs(top.x - 330) > 0:
            if (top.x - 330) > 0:
                top.x-=1
                self.gripper.x -=1

            elif (top.x - 330) < 0:
                top.x += 1
                self.gripper.x +=1
            
            self.redrawGameWindow()
            self.clock.tick(self.rate)

        ymargin = self.table.y - top.height-10
        while math.fabs(top.y - ymargin) > 0:
            if (top.y - ymargin) > 0:
                top.y-=1
                self.gripper.y -=1

            elif (top.y - ymargin) < 0:
                top.y += 1
                self.gripper.y +=1
            
            self.redrawGameWindow()
            self.clock.tick(self.rate)

        # print('moving back')
        while math.fabs(orig_y - self.gripper.y) > 0:
            if (orig_y - self.gripper.y) > 0:
                self.gripper.y += 1
            elif (orig_y - self.gripper.y) < 0:
                self.gripper.y -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)


        while math.fabs(orig_x - self.gripper.x) > 0:
            if (orig_x - self.gripper.x) > 0:
                self.gripper.x += 1
            elif (orig_y - self.gripper.x) < 0:
                self.gripper.x -= 1
            self.redrawGameWindow()
            self.clock.tick(self.rate)


    def drop_in_clutter(self, topitem):
        top = self.items[topitem]
        if not (self.gripper.holding == topitem):
            return
        self.gripper.holding = None
        top.item_on_bottom=None
        top.item_on_top=None
        top.item_at_left=None
        top.item_at_right=None
        top.on_table=False
        top.onsomething=False
        top.on_clutter_or_table=True

        for it in self.objects_list:
            if it.item_on_top == topitem:
                it.item_on_top = None
            elif it.item_on_bottom == topitem:
                it.item_on_bottom = None
            elif it.item_at_right == topitem:
                it.item_at_right = None
            elif it.item_at_left == topitem:
                it.item_at_left = None


        
        orig_x = self.gripper.x
        orig_y = self.gripper.y
        while math.fabs(top.x - top.cx) > 0:
            if (top.x - top.cx) > 0:
                top.x-=1
                self.gripper.x -=1

            elif (top.x - top.cx) < 0:
                top.x += 1
                self.gripper.x +=1
            
            self.redrawGameWindow()
            self.clock.tick(self.rate)

        while math.fabs(top.y - top.cy) > 0:
            if (top.y - top.cy) > 0:
                top.y-=1
                self.gripper.y -=1

            elif (top.y - top.cy) < 0:
                top.y += 1
                self.gripper.y +=1
            
            self.redrawGameWindow()
            self.clock.tick(self.rate)

        # print('moving back')
        while math.fabs(orig_y - self.gripper.y) > 0:
            if (orig_y - self.gripper.y) > 0:
                self.gripper.y += 1
            elif (orig_y - self.gripper.y) < 0:
                self.gripper.y -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)


        while math.fabs(orig_x - self.gripper.x) > 0:
            if (orig_x - self.gripper.x) > 0:
                self.gripper.x += 1
            elif (orig_y - self.gripper.x) < 0:
                self.gripper.x -= 1
            self.redrawGameWindow()
            self.clock.tick(self.rate)


    def put_left(self, focusitem, staticitem):
        if focusitem==staticitem:
            return
        focus = self.items[focusitem]
        static = self.items[staticitem]
        if not static.on_table:
            return
        self.gripper.holding = None
        static.item_at_left = focusitem
        focus.item_at_right = staticitem
        focus.onsomething=True
        focus.on_table = True
        orig_x = self.gripper.x
        orig_y = self.gripper.y

        margin = (static.x - focus.width)
        while math.fabs(focus.x - (static.x - focus.width)) > 0:
            if (focus.x - (static.x - focus.width)) > 0:
                focus.x -= 1
                self.gripper.x -=1

            elif (focus.x - (static.x - focus.width)) < 0:
                focus.x += 1
                self.gripper.x +=1 

            self.redrawGameWindow()
            self.clock.tick(self.rate)

        ymargin = self.table.y - focus.height-10
        while math.fabs(focus.y - ymargin) > 0:
            if (focus.y - ymargin) > 0:
                focus.y -= 1
                self.gripper.y -=1

            elif (focus.y - ymargin) < 0:
                focus.y += 1
                self.gripper.y +=1 

            self.redrawGameWindow()
            self.clock.tick(self.rate)

        # print('moving back')
        while math.fabs(orig_y - self.gripper.y) > 0:
            if (orig_y - self.gripper.y) > 0:
                self.gripper.y += 1
            elif (orig_y - self.gripper.y) < 0:
                self.gripper.y -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)


        while math.fabs(orig_x - self.gripper.x) > 0:
            if (orig_x - self.gripper.x) > 0:
                self.gripper.x += 1
            elif (orig_y - self.gripper.x) < 0:
                self.gripper.x -= 1
            self.redrawGameWindow()
            self.clock.tick(self.rate)


    def put_right(self, focusitem, staticitem):
        if focusitem==staticitem:
            return
        focus = self.items[focusitem]
        static = self.items[staticitem]
        if not static.on_table:
            return
        self.gripper.holding = None
        static.item_at_right = focusitem
        focus.item_at_left = staticitem
        focus.onsomething=True
        focus.on_table=True
        orig_x = self.gripper.x
        orig_y = self.gripper.y

        xmargin = (static.x + static.width)
        while math.fabs(focus.x - (static.x + static.width)) > 0:
            if (focus.x - (static.x + static.width)) > 0:
                focus.x -= 1
                self.gripper.x -=1

            elif (focus.x - (static.x + static.width)) < 0:
                focus.x += 1
                self.gripper.x +=1 

            self.redrawGameWindow()
            self.clock.tick(self.rate)

        ymargin = (self.table.y - focus.height-10)
        while math.fabs(focus.y - ymargin) > 0:
            if (focus.y - ymargin) > 0:
                focus.y -= 1
                self.gripper.y -=1

            elif (focus.y - ymargin) < 0:
                focus.y += 1
                self.gripper.y +=1 

            self.redrawGameWindow()
            self.clock.tick(self.rate)

        # print('moving back')
        while math.fabs(orig_y - self.gripper.y) > 0:
            if (orig_y - self.gripper.y) > 0:
                self.gripper.y += 1
            elif (orig_y - self.gripper.y) < 0:
                self.gripper.y -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)


        while math.fabs(orig_x - self.gripper.x) > 0:
            if (orig_x - self.gripper.x) > 0:
                self.gripper.x += 1
            elif (orig_y - self.gripper.x) < 0:
                self.gripper.x -= 1
            self.redrawGameWindow()
            self.clock.tick(self.rate)


    def missed_pick(self):
        orig_x = self.gripper.x
        orig_y = self.gripper.y 
        while math.fabs(100 - (self.gripper.x+26)) > 0:
            if 100 - (self.gripper.x+26) > 0:
                self.gripper.x += 1
            elif 100 - (self.gripper.x+26) < 0:
                self.gripper.x -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)
        # print('done moving left')

        while math.fabs(400 - (self.gripper.y+90)) > 0:
            if 400 - (self.gripper.y+90) > 0:
                self.gripper.y += 1
            elif 400 - (self.gripper.y+90) < 0:
                self.gripper.y -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)

        # print('done moving right')
        # time.sleep(2)
        # print('moving back')
        while math.fabs(orig_y - self.gripper.y) > 0:
            if (orig_y - self.gripper.y) > 0:
                self.gripper.y += 1
            elif (orig_y - self.gripper.y) < 0:
                self.gripper.y -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)


        while math.fabs(orig_x - self.gripper.x) > 0:
            if (orig_x - self.gripper.x) > 0:
                self.gripper.x += 1
            elif (orig_y - self.gripper.x) < 0:
                self.gripper.x -= 1

            self.redrawGameWindow()
            self.clock.tick(self.rate)













if __name__ == '__main__':
    args = sys.argv
    if len(args) != 3:
        print("Arguments should be level_of_certainty, clutter_strategy and init_order_num")
    else:        
        uncertainty = args[1]
        clutter_strategy = False if args[2]=="optimistic" else True
        order = np.random.randint(4)#int(args[3])
        g = environment(uncertain=uncertainty, 
                        declutter=clutter_strategy, 
                        order=order)
        g.run()
        # g.run_simulation(g.domain_path, g.problem_path)
        # g.clutter_optimistic_planning()
        # g.declutter_before_clutter_planning()
        # while True:
        #     g.redrawGameWindow()
















