# D:/Python/python.exe -m pip install -U twitchio
# D:/Python/python.exe -m pip install -U pillow

# BANK ACCOUNT SCRIPT FOR VSPQ
# PROBLEMS - refereshes are visible on stream
# UI Layout could be improved
# Make sure to make this account a mod.

# SUGGESTED PAYOUTS
# - user wins race or completes a speedrun: 150
# - user participates in a race and loses or runs a speedrun, but fails: 50
# - user wins a small game (it came from itch), hosts a non-competitive event, or says something funny in chat: 25


from twitchio.ext import commands
from PIL import Image, ImageTk
from tkinter import Tk, ttk, Label, Frame, LEFT
import time, datetime, random, threading, asyncio, json

# set the vpsq channel name here.
VPSQ_CHANNEL_NAME = "vpsqofficial"
# type in admin name
ADMIN = ""
# make UI bigger
UI_SCALE = 2

class Bot(commands.Bot):

    # bot setup stuff
    def __init__(self):
        super().__init__(token='YOUR_TOKEN', prefix='!', initial_channels=[VPSQ_CHANNEL_NAME])

        # === STATE VARS ===
        # user data. searched by name.
        # {cash: N, prizes: [,]}
        self.users = {}

        # how much cash has been donated to vinny
        self.vinny_donations = 0

        # when was the last cash drop? 
        self.cash_drop_timestamp = 0

        # when is the next cash drop?
        self.cash_drop_next= 0

        # auction timestamp
        self.auction_timestamp = 0
        # current item to auction
        self.item_to_auction = None
        # current item bid
        self.item_bid = [None, None]

        self.AUCTION_TIME = 60 * 5

        self.NEXT_DROP_MIN = 60 * 10
        self.NEXT_DROP_MAX = 60 * 90
        self.stimmy_warned = False
        self.stimmy_closed = False

        # who got their stimmy?        
        self.got_stimmy = {}

        # how long can users recieve cash during a drop?
        self.CASH_DROP_DURATION = 120
        self.WARN_TIME = 30

        self.auction_items_available = ["CONTROLLER_BLASTER","FLAMINGO_LAWNMOWER","GABENS_GIBUS","GAMER_GOGGLES","INFINITY_TOASTER","KFC_12TH","LITTLE_IRON","ZOOMER_DICTIONARY"]

    # we are logged in, make the UI, load data from file.
    async def event_ready(self):
        print(f'Logged in as | {self.nick}')
        print(f'User id is | {self.user_id}')
        self.load_user_data()

        # run the main loops to update UI
        thd = threading.Thread(target=self.tk_ui)   # gui thread
        thd.daemon = True  # background thread will exit if main thread exits
        thd.start()  # start tk loop

    def tk_ui(self):
        # window setup and style
        self.ui_root = Tk()
        self.frame = Frame(self.ui_root)
        self.ui_root.resizable(False,False)
        self.ui_root.geometry(str(UI_SCALE*200)+"x"+str(UI_SCALE*600))
        self.ui_update_loop()
        # set title of window
        self.ui_root.title("BANK OF VIDYA (POWERED BY JAVA 3.0)")
        self.ui_root.mainloop()

    def save_user_data(self):
        with open('accounts.json', 'w', encoding='utf-8') as f:
            save = {"users":self.users, "donations":self.vinny_donations}
            json.dump(save, f, ensure_ascii=False, indent=4)
    
    def load_user_data(self):
        try:
            with open('accounts.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.users = data["users"]
                self.vinny_donations = data["donations"]

            # remove all the items already owned by users
            for user in self.users:
                for item in self.users[user]["prizes"]:
                    if(item in self.auction_items_available):
                        self.auction_items_available.remove(item)
        except:
            print("no account file exists, starting from start")

    # checks for a user, makes them if they don't exist.
    def user_account(self,name):
        if(name not in self.users):
            self.users[name] = {"cash": 0, "prizes": []}
        return self.users[name]
        
    def ui_update_loop(self):
        self.save_user_data()

        self.frame.destroy()
        self.frame = Frame(self.ui_root)

        self.frame.pack()
        # headers
        h1 = Label(self.frame, text="BANK OF VIDYA")
        h1.config(font = ("Comic Sans MS", UI_SCALE*12, "bold"))
        h1.pack()

        h2 = Label(self.frame, text="official database")
        h2.config(font = ("Comic Sans MS", UI_SCALE*8, "bold"))
        h2.pack()

        h3 = Label(self.frame, text=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        h3.config(font = ("Comic Sans MS", UI_SCALE*8, "bold"))
        h3.pack()

        self.donationbar = ttk.Progressbar(
            self.frame,
            orient='horizontal',
            mode='determinate',
            maximum = 5000,
            length=190
        )
        self.donationbar["value"] = (self.vinny_donations)
        self.donationbar.pack()

        d = Label(self.frame, text=f"{self.vinny_donations} vidyabucks\nhave been donated to vinny.")
        d.config(font = ("Comic Sans MS", UI_SCALE*8, "bold"))
        d.pack()

        # ui element for stimmy jimmy
        if(time.time() - self.cash_drop_timestamp < self.CASH_DROP_DURATION):
            cash_drop = Label(self.frame, text="STIMMY JIMMY ACTIVE!",fg='#0f0')
            cash_drop.config(font = ("Comic Sans MS", UI_SCALE*10, "bold"))
            cash_drop.pack()

            cash_drop = Label(self.frame, text=f"TIME LEFT {int(self.CASH_DROP_DURATION - (time.time() - self.cash_drop_timestamp))}",fg='#0f0')
            cash_drop.config(font = ("Comic Sans MS", UI_SCALE*8, "bold"))
            cash_drop.pack()

        # ui element for auction
        if(self.item_to_auction != None):
            cash_drop = Label(self.frame, text="AUCTION STARTED FOR",fg='#00f')
            cash_drop.config(font = ("Comic Sans MS", UI_SCALE*10, "bold"))
            cash_drop.pack()

            cash_drop = Label(self.frame, text=f"{self.item_to_auction}",fg='#00f')
            cash_drop.config(font = ("Comic Sans MS", UI_SCALE*10, "bold"))
            cash_drop.pack()

            if(self.item_bid[0] != None):
                cash_drop = Label(self.frame, text=f"CURRENT BID IS $V{self.item_bid[1]}",fg='#00f')
                cash_drop.config(font = ("Comic Sans MS", UI_SCALE*10, "bold"))
                cash_drop.pack()

                cash_drop = Label(self.frame, text="MADE BY " + self.item_bid[0],fg='#00f')
                cash_drop.config(font = ("Comic Sans MS", UI_SCALE*10, "bold"))
                cash_drop.pack()

            else:
                cash_drop = Label(self.frame, text="BID NOW!!!",fg='#00f')
                cash_drop.config(font = ("Comic Sans MS", UI_SCALE*10, "bold"))
                cash_drop.pack()

            cash_drop = Label(self.frame, text=f"TIME LEFT {int(self.AUCTION_TIME - (time.time() - self.auction_timestamp))}",fg='#00f')
            cash_drop.config(font = ("Comic Sans MS", UI_SCALE*8, "bold"))
            cash_drop.pack()

        # ui element for balances and prizes
        aslist =  list(self.users.items())
        aslist.sort(key= lambda val: -val[1]["cash"]) 
        for user in aslist:
            name = user[0]
            prizes = user[1]["prizes"]
            money = user[1]["cash"]
            u = Label(self.frame, text=f"{name}\nV${money}")
            u.config(font = ("Comic Sans MS", UI_SCALE*8, "bold"))
            u.pack()

            if(len(prizes) > 0):
                u = Label(self.frame, text=f"{name}'s items:")
                u.config(font = ("Comic Sans MS", UI_SCALE*8, "bold"))
                u.pack()
            # load an image for each prize the user has and stick it into ui
            for prize in prizes:
                img = Image.open(f"prizes/{prize}.png")
                img = img.resize((UI_SCALE*40, UI_SCALE*40), Image.LANCZOS)
                img = ImageTk.PhotoImage(img)
                panel = Label(self.frame, image = img)
                panel.image = img
                # This will list items downwards, which is probably not ideal.
                # At least chat made certain to let me know that it wasn't.
                panel.pack()

        # Timers
        # check if time to launch deposit
        if(time.time() - self.cash_drop_timestamp > self.cash_drop_next):
            self.cash_drop_timestamp = time.time()
            self.cash_drop_next = random.randrange(self.NEXT_DROP_MIN,self.NEXT_DROP_MAX)
            self.got_stimmy = {}
            self.stimmy_warned = False
            self.stimmy_closed = False
            print("starting cash drop!")
            asyncio.run(self.stimmy_time())

        # check if time to warn about stimmy jimmy leaving.
        if(time.time() - self.cash_drop_timestamp > self.WARN_TIME and not self.stimmy_warned):
            self.stimmy_warned = True
            asyncio.run(self.stimmy_warn())

        # check if time to warn about stimmy jimmy leaving.
        if(time.time() - self.cash_drop_timestamp > self.CASH_DROP_DURATION and not self.stimmy_closed):
            self.stimmy_closed = True
            asyncio.run(self.stimmy_close())

        # check if the auction ended.
        if(time.time() - self.auction_timestamp > self.AUCTION_TIME and self.item_to_auction != None):
            asyncio.run(self.auction_winner(self.item_bid[0],self.item_to_auction))
            if(self.item_bid[0] is not None):
                self.user_account(self.item_bid[0])["prizes"].append(self.item_to_auction)
                self.user_account(self.item_bid[0])["cash"] -= self.item_bid[1]
                self.item_to_auction = None
                self.item_bid = [None, None]
            else:
                self.item_to_auction = None
                self.item_bid = [None, None]

        self.ui_root.update()
        self.ui_root.after(1000, self.ui_update_loop)


    async def stimmy_time(self):
        await self.connected_channels[0].send("Stimmy Jimmy is here!!!! Kreygasm")
        await asyncio.sleep(2)
        await self.connected_channels[0].send("Type !deposit to get the stimmy!")  

    async def stimmy_warn(self):
        await self.connected_channels[0].send("Stimmy Jimmy is leaving soon!")
        await asyncio.sleep(2)
        await self.connected_channels[0].send("Type !deposit to get the stimmy!")  

    async def stimmy_close(self):
        await self.connected_channels[0].send("Stimmy Jimmy is gone. Say Goodbye!")

    async def auction_winner(self,name,item):
        if(name is None):
            await self.connected_channels[0].send(f"No one wanted the {item}...")
        else:
            await self.connected_channels[0].send(f"The auction ended and {name} won the {item}!")

    async def event_message(self, message):
        if message.echo:
            return

        args = message.content.split()
        author = message.author.display_name
        result = None
        if(len(args) > 0):
            if(args[0] == "!bid"):
                result = self.bid(author,args)
            if(args[0] == "!donate"):
                result = self.donate(author,args)
            if(args[0] == "!deposit"):
                result = self.deposit(author,args)
            if(args[0] == "!award"):
                result = self.award(author,args)
            if(args[0] == "!auction"):
                result = self.auction(author,args)
            if(args[0] == "!balance"):
                result = self.balance(author,args)
            if(args[0] == "!help"):
                result = self.help(author,args)
            
        if(result != None):
            await self.connected_channels[0].send(result)   

    # place a bid on a current item [WORKS]
    def bid(self, author, args):
        try:
            if(self.item_to_auction == None):
                return f"{author}, there's nothing to bid on, you ducker."
            
            amt = int(args[1])
            if(amt <= 0):
                return f"{author}, this isn't a charity."

            if(amt > self.user_account(author)["cash"]):
                return f"Sorry {author}, come back when you're a little, mmmm, richer."
            
            no_bid = self.item_bid[0] == None
            if(no_bid):
                self.item_bid = [author, amt]
                return f"{author} has started the bidding at $V{amt}!"

            high_bid = amt > self.item_bid[1]
            if(high_bid):
                self.item_bid = [author, amt]
                return f"{author} has bid $V{amt} on {self.item_to_auction}!"
            else:
                return f"{author}, the bid is currently $V{self.item_bid[1]}."
    
        except:
            return "Bid failed, try !bid [AMOUNT]"           

    # donate money to vinny [WORKS]
    def donate(self, author, args):
        try:
            value = int(args[1])
            act = self.user_account(author)

            if(self.item_bid[0] != None and author == self.item_bid[0]):
                return f'{author}, you cannot donate while you have an active bid.'

            if(value == 0):
                return f'{author} tried to donate nothing. But why?'
            if(value < 0):
                return f'{author} tried to steal from Vinny! For shame!'

            if(act["cash"] >= value):
                self.vinny_donations += value
                act["cash"] -= value
                return f'{author} donated {value} vidya bucks!'
            else:
                return f'{author} tried to donate $V{value} but they were too poor.'
        except:
            return "Donation failed, try !donate [AMOUNT]"        

    # get a deposit [WORKS]
    def deposit(self, author, args):
        if(time.time() - self.cash_drop_timestamp < self.CASH_DROP_DURATION):
            if(author in self.got_stimmy):
                return f'{author}, you can only get one Stimmy per Jimmy.'

            self.got_stimmy[author] = True
            reward = random.randrange(1,200)
            self.user_account(author)["cash"] += reward
            return f"{author} got a stimmy of $V{reward}!"
        else:
            return f"{author}, no stimmy is available right now."
    
    # award points to someone [WORKS] (logan only)
    def award(self, author, args):
        try:
            if(author == ADMIN):
                if((len(args) == 3) and (args[1] in self.users)) :
                    self.users[args[1]]["cash"] += int(args[2])
                    return f"{args[2]} vidya bucks have been awarded to " + args[1] + "!"
                else:
                    return "Award failed, try !award [USERNAME] [AMOUNT]"
            else:
                return "You aren't authorized to do this."
        except:
            return "Award failed, try !award [USERNAME] [AMOUNT]"
    
    # begin auction [WORKS] (logan only)
    def auction(self, author, args):
        if(author == ADMIN):
            if(self.item_to_auction == None and args[1] in self.auction_items_available):
                item = args[1]
                self.auction_items_available.remove(args[1])
                self.auction_timestamp = time.time()
                self.item_to_auction = item
                self.item_bid = [None, None]
                return f"The auction of {item} has started!!! Type !bid [AMOUNT] to make a bid."
            else:
                return "Auction failed, try !auction [ITEMNAME]"
        else:
            return "You aren't authorized to do this."

    def balance(self,author,args):
        act = self.user_account(author)
        return f"{author}, your balance is $V" + str(act["cash"]) + "."

    def help(self,author,args):
        return "You can always use !donate and !balance, this will also open your account if you don't have one. Use !deposit when Stimmy Jimmy is active. !bid is used for auctions. Admins may use !award, !auction."


bot = Bot()
bot.run()