from flask import Flask, render_template, Response, jsonify, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import string
import random
from mail import send_mail ,send_confirmation_mail,send_cancellation_mail

app = Flask(__name__)
app.config['SECRET_KEY']='KGPGH@123'
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///oghbs.db'
db = SQLAlchemy(app) 

otpc=0
res=""
ghid=-1
cost=0
currentuserid=-1
currentusertype=""
checkindate = datetime.now()
checkoutdate = datetime.now()
foodId = '0'
amenitiesId='0'
roomId = 0
rooms = []
avail = []
days = []
urls = []
roomAvail = []


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    email = db.Column(db.String(50))
    username = db.Column(db.String(50),unique=True)
    password = db.Column(db.String(20))
    address = db.Column(db.String(200))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    rollstd = db.Column(db.String(20),nullable=True,unique=True)
    usertype = db.Column(db.String(50))
    def __repr__(self):
        return '<Name %r>' % self.id


class GuestHouse(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(100))
    description = db.Column(db.String(100))


class Rooms(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    floor = db.Column(db.Integer)
    roomtype = db.Column(db.String(50))
    description = db.Column(db.String(100)) 
    status = db.Column(db.String(100))
    ghId = db.Column(db.Integer)
    pricePerDay = db.Column(db.Integer)
    occupancy = db.Column(db.Integer)
    ac = db.Column(db.Integer)


class FoodOptions(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pricePerDay = db.Column(db.Integer)
    type = db.Column(db.String(40))

class Amenities(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pricePerDay = db.Column(db.Integer)
    type = db.Column(db.String(40))


class BookingQueue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bookingIds = db.Column(db.String(40))


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    userId = db.Column(db.Integer)
    roomId = db.Column(db.Integer)
    foodId = db.Column(db.Integer)
    amenitiesId = db.Column(db.Integer)
    checkindate = db.Column(db.DateTime)
    checkoutdate = db.Column(db.DateTime)
    dateOfBooking = db.Column(db.DateTime)
    confirmation = db.Column(db.Integer)
    feedback = db.Column(db.String(100))

class Authentication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    val = db.Column(db.Integer)

class Payment(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    amount=db.Column(db.Float)
    paymentid=db.Column(db.String(20))

class Cash(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    paymentid=db.Column(db.String(20))
    amountc=db.Column(db.Float,db.ForeignKey('payment.amount'))

class Creditcard(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    paymentid=db.Column(db.String(20))
    name=db.Column(db.String(30))
    amountcc=db.Column(db.Float,db.ForeignKey('payment.amount'))
   

class Upi(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    paymentid=db.Column(db.String(20))
    upiid=db.Column(db.String(20))
    amountu=db.Column(db.Float,db.ForeignKey('payment.amount'))


    
def checkAvailable(room):
    global checkindate,checkoutdate
    i=(checkindate-datetime.now()).days
    checkinindex=i
    j=(checkoutdate-datetime.now()).days
    checkoutindex=j
    if checkinindex <0 or checkoutindex<0:
        return False
    for x in room.status[checkinindex:checkoutindex+1]:
        if x=='1':
            return False
    return True
    
def updatestatus(roomid,checkIndate,checkOutdate,val):
    temp=(checkIndate -datetime.now()).days
    checkinindex=max(0,temp)
    temp=(checkOutdate-datetime.now()).days
    checkoutindex=temp
    dur=checkoutindex-checkinindex+1
    stat=""
    for i in range(dur):
        stat+=val
    room=Rooms.query.filter_by(id=roomid).first()
    newstat = room.status[:checkinindex] + stat + room.status[checkoutindex+1:]
    newroom=room
    db.session.delete(newroom)
    room.status = newstat
    db.session.add(room)
    db.session.commit()
    
def checkBooking(bookingid):
    booking = Booking.query.filter_by(id=bookingid).first()
    if booking is None:
       return False
    room = Rooms.query.filter_by(id=booking.roomId).first()
    checkIndate=booking.checkindate
    checkOutdate=booking.checkoutdate
    temp=(checkIndate - datetime.now()).days
    checkinindex = temp
    temp = (checkOutdate -datetime.now()).days
    checkoutindex=temp
    if checkinindex<0 or checkoutindex<0:
          return False 
    for i in room.status[checkinindex : checkoutindex+1]:
        if i=='1':
           return False
    user=User.query.filter_by(id=booking.userId).first()
    newbook=booking
    db.session.delete(newbook)
    booking.confirmation =1
    db.session.add(booking)
    db.session.commit()
    text="Booking id :"+str(booking.id)+"\nStatus :Confirmed"
    send_confirmation_mail("Previous Booking in Queue is Comfirmed", text, user.email)
    updatestatus(booking.roomId,checkIndate,checkOutdate,'1')
    return True
    

def AddBaseAdmin():
    st='0'
    for i in range(100):
        st=st+'0'
    
    rooms = [Rooms(id=1, floor=0, roomtype="D/B NON AC Rooms", description="Double Bed", status=st, ghId=0, pricePerDay=800, occupancy=2, ac=1),
                Rooms(id=2, floor=0, roomtype="D/B AC Rooms", description="Double Bed", status=st, ghId=0, pricePerDay=1000, occupancy=2, ac=0),
                Rooms(id=3, floor=1, roomtype="Suite Rooms", description="Single Bed", status=st, ghId=0, pricePerDay=2000, occupancy=2, ac=0),
                Rooms(id=4, floor=2, roomtype="Meeting Room", description="for meeting", status=st, ghId=0, pricePerDay=5000, occupancy=10, ac=1),
                Rooms(id=5, floor=0, roomtype="D/B AC Rooms", description="Double Bed", status=st, ghId=2, pricePerDay=600, occupancy=3, ac=1),
                Rooms(id=6, floor=0, roomtype="D/B NON AC Rooms", description="Double Bed", status=st, ghId=2, pricePerDay=400, occupancy=3, ac=0),
                Rooms(id=7, floor=2, roomtype="Dormitory Beds AC", description="Single Bed", status=st, ghId=2, pricePerDay=250, occupancy=1, ac=1)]

    for i in rooms:
        db.session.add(i)
        db.session.commit()

    houses = [GuestHouse(id=0, address="IIT Kharagpur, Kharagpur 721302", description="Technology Guest House"),
                GuestHouse(id=1, address="IIT Kharagpur, Kharagpur 721302", description="Visveswaraya Guest House"),
                GuestHouse(id=2, address="HC Block, Sector-III Salt Lake City Kolkata-700106", description="Kolkata Guest House")]

    for i in houses:
        db.session.add(i)
        db.session.commit()

    foods = [FoodOptions(id=0, pricePerDay=0, type='none'),
                FoodOptions(id=1, pricePerDay=200, type='North Indian Veg'),
                FoodOptions(id=2, pricePerDay=300, type='North Indian Non-Veg'),
                FoodOptions(id=3, pricePerDay=250, type='South Indian Veg'),
                FoodOptions(id=4, pricePerDay=350, type='South Indian Non-Veg'),
                FoodOptions(id=5, pricePerDay=300, type='Chinese'),
                FoodOptions(id=6, pricePerDay=450, type='Italian'),
                FoodOptions(id=7, pricePerDay=400, type='Continental')]

    for i in foods:
        db.session.add(i)
        db.session.commit()

    amenities = [Amenities(id=0,pricePerDay=0, type="none"),
                Amenities(id=1,pricePerDay=200, type="Gym"),
                Amenities(id=2,pricePerDay=200, type="Swimming Pool"),
                Amenities(id=3,pricePerDay=100, type="Library"),
                Amenities(id=4,pricePerDay=100, type="Laundry"),
                Amenities(id=5, pricePerDay=400,type="Movie Hall"),
                Amenities(id=6, pricePerDay=800,type="Bar")]

    for i in amenities:
        db.session.add(i)
        db.session.commit()
    admin = User(id=0, firstname="devichand",lastname="budagam", email="devichand579@gmail.com",username="devichand", password="Devichand@123", address="Bhadrachalam , Telangana", age=19, gender="Male", rollstd="GH001",usertype="Admin")
    val=Authentication(id=0,val=1)
    db.session.add(admin)
    db.session.add(val)
    db.session.commit()


if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["cache-control"]="no-cache, no-store,must-revalidate, public, max-age=0"
        response.headers["Expires"]=0
        response.headers["pragma"]="no-cache"
        return response

@app.before_first_request
def create_tables():
     db.drop_all()
     db.create_all()
     AddBaseAdmin()
     

@app.route('/', methods=["POST", "GET"])
def welcome():
    if request.method == "POST":
        print(request.form['username'])
        user = User.query.filter_by(username=request.form['username']).first()
        print(request.form['password'])
        global currentuserid,currentusertype
        if user is not None and user.password == request.form['password']:
            currentuserid = user.id
            currentusertype = user.usertype
            if user.usertype =="Admin":
                auth = Authentication.query.filter_by(id=user.id).first()
                print(auth.val)
                if auth.val != 1:
                    return render_template('index.html',flag=auth.val)
                return admin()
            else:
                auth = Authentication.query.filter_by(id=user.id).first()
                print(auth.val)
                if auth.val != 1:
                    return render_template('index.html',flag=auth.val)
                return render_template('calender.html')
        else:
            return render_template('index.html',flag=1)
    return render_template('index.html',flag=-1)



@app.route('/signup', methods=["POST", "GET"])
def sign_up():
    global otp
    if request.method == "POST":
        newid = User.query.count()
        username = request.form['username']
        password = request.form['password']
        firstname= request.form['first_name']
        lastname= request.form['last_name']
        email = request.form['email']
        address = request.form['address1']+", "+request.form['address2']+", "+request.form['city']+","+request.form['state']        
        gender = request.form['gender']            
        age = request.form['age']    
        rollStd = request.form['roll']
        usertype = request.form['role']
              
        checkusername = User.query.filter_by(username=request.form['username']).first()
        if checkusername is None:
            pass
        else:
            return render_template('regform.html', flag=0)
        # push to db
        try:
            newUser = User(id=newid, firstname=firstname,lastname=lastname, email=email, username=username, password=password, address=address, age=age, gender=gender, rollstd=rollStd, usertype=usertype)
            newAuthReq = Authentication(id=newid, val=0)
            db.session.add(newUser)
            db.session.add(newAuthReq)
            db.session.commit()
            print("User added successfully")
            i=User.query.count()-1
            user=User.query.filter_by(id=i).first()
            otp=send_mail("OTP for registration","Enter the otp for verification",user.email)
            return redirect('/otp')
        except:
            print("Could not add new user to the database")
    return render_template('regform.html', flag=1)


@app.route('/otp', methods=['POST','GET'])
def check():
    if request.method =="POST":
        i=User.query.count()-1
        newAuthReq = Authentication.query.filter_by(id=i).first()
        user=User.query.filter_by(id=i).first()
        if otp==int(request.form['otp']):
            return render_template('index.html',flag=3)
        else:
            db.session.delete(user)
            db.session.delete(newAuthReq)
            print("User deleted successfully")
            db.session.commit()
            return render_template('index.html',flag=4)
    return render_template('otp.html')

    

@app.route('/admin', methods=["POST", "GET"])
def admin():
    authRequests = []
    requests = Authentication.query.filter_by(val=0)
    for req in requests:
        authRequests.append(User.query.filter_by(id=req.id).first())
    return render_template('admin.html', users=authRequests)


@app.route('/adminDates', methods=["POST", "GET"])
def adminDates():
    if request.method == "POST":
        global checkindate
        global checkoutdate
        global ghid
        checkindate = datetime.strptime(request.form['checkintime'], '%Y-%m-%d')
        checkoutdate = datetime.strptime(request.form['checkouttime'], '%Y-%m-%d')
        ghid=int(request.form['ghid']) 
        return redirect('/rooms')
    return render_template('adminCalendar.html')

@app.route('/adminHistory', methods=["POST", "GET"])
def adminHistory():
    bookings = Booking.query.all()
    rooms = [Rooms.query.filter_by(id=i.roomId).first() for i in bookings]
    user = [User.query.filter_by(id=i.userId).first() for i in bookings]
    cost = [Payment.query.filter_by(id=i.id).first() for i in bookings]
    return render_template('adminPrevBooking.html', bookings=bookings, user=user, rooms=rooms, prices=cost)


@app.route('/authorize/<userId>/<desc>', methods=["POST", "GET"])
def authorize(userId, desc):
    userId = int(userId)
    desc = int(desc)
    user=User.query.filter_by(id=userId).first()
    userVal = Authentication.query.filter_by(id=userId).first()
    userVal.val = desc
    db.session.commit()
    return admin()

@app.route('/profile', methods=["POST", "GET"])
def profile():
    user = User.query.filter_by(id=currentuserid).first()
    return render_template('profile.html', user=user)

@app.route('/rooms', methods=["POST", "GET"])
def show_rooms():
    global checkindate
    global checkoutdate
    global foodId
    global amenitiesId
    global rooms
    global avail
    global days
    global urls
    global roomAvail
    rooms=[]
    print("booking1")
    temp=Rooms.query.all()
    for i in temp:
        if ghid == i.ghId:
            rooms.append(i)
    if 'foodId' in request.form:
        foodId = request.form['foodId']
        print(foodId)
    if 'amenitiesId' in request.form:
        amenitiesId = request.form['amenitiesId']
        print(amenitiesId)
    if checkindate is not None and checkoutdate is not None:
        checkInDate = checkindate
        checkOutDate = checkoutdate
        if datetime.now() <= checkInDate <= checkOutDate and (checkOutDate-datetime.now()).days < 100:
            pass
        else:
            if currentusertype== "Admin":
                return render_template('adminCalendar.html', flag=0)
            return render_template('calender.html', flag=0)
        print("booking2")
        print(checkInDate)
        print(checkOutDate)
        idx1 = int(foodId)
        foodItem = FoodOptions.query.filter_by(id=idx1).first()
        idx2 = int(amenitiesId)
        amenity = Amenities.query.filter_by(id=idx2).first()
        if idx1!= 0:
            if foodItem is not None:
                for i in rooms:
                    i.pricePerDay += foodItem.pricePerDay
        if idx2 != 0:
            if amenity is not None:
                for i in rooms:
                    i.pricePerDay += amenity.pricePerDay
        curdate = datetime.now()
        startDay = max(curdate, checkInDate-timedelta(days=3)).day - curdate.day
        startIdx = startDay
        startdate = max(curdate, checkInDate-timedelta(days=3))
        days = []
        for i in range(7):
            temp = startdate + timedelta(days=i)
            days.append(temp.day)
        avail = []
        for room in rooms:
            temp = []
            urls.append("/room/"+str(room.id))
            for j in range(7):
                temp.append(int(room.status[startIdx+j]))
            avail.append(temp)

    print(avail)
    print(len(rooms))
    roomAvail = [0]*len(rooms)
    for i, room in enumerate(rooms):
        roomAvail[i] = 1 if checkAvailable(room) else 0
    print(roomAvail)
    if currentusertype== "Admin":
        return render_template('adminBooking.html', rooms=rooms, avail=avail, days=days, urls=urls, roomAvail=roomAvail)
    return render_template('Booking.html', rooms=rooms, avail=avail, days=days, urls=urls, foodId=foodId, amenitiesId=amenitiesId, roomAvail=roomAvail)

@app.route('/room/<roomid>', methods=["POST", "GET"])
def room(roomid):
    global roomId
    global cost
    global otpc
    roomId = int(roomid)
    print(roomId)
    bookedroom = Rooms.query.filter_by(id=roomId).first()
    bookedfood = FoodOptions.query.filter_by(id=foodId).first()
    bookedamenity= Amenities.query.filter_by(id=amenitiesId).first()
    roomCost = bookedroom.pricePerDay*((checkoutdate-checkindate).days+1)
    foodCost = 0
    amenityCost=0
    if bookedfood is not None:
        foodCost = bookedfood.pricePerDay*((checkoutdate-checkindate).days+1)
    if bookedamenity is not None:
        amenityCost = bookedamenity.pricePerDay*((checkoutdate-checkindate).days+1)
    diff=(checkindate-datetime.now()).days
    cost = (roomCost+foodCost+ amenityCost)
    if diff>=30 :
       cost=cost*0.85
    if diff>=15 and diff<30 :
       cost =cost*0.9
    cost= 0.2*cost
    user=User.query.filter_by(id=currentuserid).first()
    otpc=send_mail("OTP for payment verification","Enter the otp for verification", user.email)
    return render_template('payment.html', roomPrice=roomCost, foodPrice=foodCost,amenityPrice=amenityCost, payable=cost)

@app.route('/cash', methods=["POST", "GET"])
def cash():
    global otpc
    global res
    print(otpc)
    if request.method == "POST":
        if otpc == int(request.form['otpc']):
            id=Cash.query.count()
            res = ''.join(random.choices(string.ascii_uppercase +string.digits, k=16))
            print(res)
            newcash=Cash(id=id,amountc=cost,paymentid=res)
            id=Payment.query.count()
            newpayment=Payment(id=id, amount=cost, paymentid=res)
            db.session.add(newpayment)
            db.session.add(newcash)
            db.session.commit()
            return redirect('/paymentComplete')
        else:
            user=User.query.filter_by(id=currentuserid).first()
            otpc=send_mail("OTP for payment verification","Enter the otp for verification", user.email)
            return render_template('cash.html', flag=1)
    print(roomId)
    return render_template('cash.html', flag=0)

@app.route('/credit', methods=["POST", "GET"])
def credit():
    global otpc
    global res
    if request.method == "POST":
        if otpc==request.form['otp']:
            name=request.form['name']
            id=Creditcard.query.count()
            res = ''.join(random.choices(string.ascii_uppercase +string.digits, k=16))
            print(res)
            newcredit=Creditcard(id=id, name=name, amountcc=cost, paymentid=res)
            id=Payment.query.count()
            newpayment=Payment(id=id, amount=cost, paymentid=res)
            db.session.add(newpayment)
            db.session.add(newcredit)
            db.session.commit()
            return redirect('/paymentComplete')
        else:
            user=User.query.filter_by(id=currentuserid).first()
            otpc=send_mail("OTP for payment verification","Enter the otp for verification", user.email)
            return render_template('credit.html', flag=1)
    return render_template('credit.html', flag=0)

@app.route('/upi', methods=["POST", "GET"])
def upi():
    global otpc
    global res
    if request.method == "POST":
        if otpc== int(request.form['otp']):
            upiid=request.form['upi']
            id=Upi.query.count()
            res = ''.join(random.choices(string.ascii_uppercase +string.digits, k=16))
            print(res)
            newupi=Upi(id=id, upiid=upiid, amountu=cost, paymentid=res)
            id=Payment.query.count()
            newpayment=Payment(id=id, amount=cost, paymentid=res)
            db.session.add(newpayment)
            db.session.add(newupi)
            db.session.commit()
            return redirect('/paymentComplete')
        else:
            user=User.query.filter_by(id=currentuserid).first()
            otpc=send_mail("OTP for payment verification","Enter the otp for verification", user.email)
            return render_template('upi.html', flag=1)
    return render_template('upi.html', flag=0)

@app.route('/dates', methods=["POST", "GET"])
def dates():
    if request.method == "POST":
        global checkindate
        global checkoutdate
        global ghid
        checkindate = datetime.strptime(request.form['checkintime'], '%Y-%m-%d')
        checkoutdate = datetime.strptime(request.form['checkouttime'], '%Y-%m-%d')
        ghid=int(request.form['ghid']) 
        return redirect('/rooms')
    return render_template('calender.html')


@app.route('/history', methods=["POST", "GET"])
def history():
    currentDate = datetime.now()
    userBookings = Booking.query.filter_by(userId=currentuserid).all()
    for i in userBookings:
        if currentDate > i.checkoutdate + timedelta(30):
            temp=i
            db.session.delete(temp)
            i.confirmation = 4
            db.session.add(i)
            db.session.commit() 
    paymentids=[Payment.query.filter_by(id=i.id).first() for i in userBookings]  
    rooms = [Rooms.query.filter_by(id=i.roomId).first() for i in userBookings]
    costs = [Payment.query.filter_by(id=i.id).first() for i in userBookings]
    return render_template('prevBooking.html', bookings=userBookings, paymentids=paymentids, rooms=rooms, prices=costs)


@app.route('/paymentComplete', methods=["POST", "GET"])
def paymentComplete():
    global food 
    global amenity
    global gh
    print("Payment Completed")
    id = Booking.query.count()
    curRoom = Rooms.query.filter_by(id=roomId).first()
    if checkAvailable(curRoom):
        conf = 1
    else:
        conf = 0
    queueIds = BookingQueue.query.filter_by(id=roomId).first()
    if conf == 1:
        print(curRoom.status)
        updatestatus(roomId, checkindate, checkoutdate, '1')
        curRoom = Rooms.query.filter_by(id=roomId).first()
        print(curRoom.status)
    else:
        if queueIds is None:
            print("first")
            newId = str(id)
            print(newId)
            if len(newId) == 1:
                newId = newId.rjust(4, '0')
                stat = newId
                stat = stat.ljust(40, '0')
            if len(newId) == 2:
                newId = newId.rjust(4, '0')
                stat = newId
                stat = stat.ljust(40, '0')
            if len(newId) == 3:
                newId = newId.rjust(4, '0')
                stat = newId
                stat = stat.ljust(40, '0')
            if len(newId) == 4:
                stat = newId
                stat = stat.ljust(40, '0')
            temp = BookingQueue(id=roomId, bookingIds=stat)
            print(stat)
            db.session.add(temp)
        else:
            print("next")
            pos = 36
            newId = str(id)
            if len(newId) == 1:
                newId = newId.rjust(4, '0')
            if len(newId) == 2:
                newId = newId.rjust(4, '0')
            if len(newId) == 3:
                newId = newId.rjust(4, '0')
            for idx in range(0, 40, 4):
                checker = queueIds.bookingIds[idx:idx+4]
                print(checker)
                if int(checker) == 0:
                    pos = idx
                    break
            newstat = queueIds.bookingIds[:pos] + newId + (queueIds.bookingIds[pos+4:] if pos+4 < 39 else "")
            temp=queueIds
            db.session.delete(temp)
            queueIds.bookingIds = newstat
            db.session.add(queueIds)

    newBooking = Booking(id=id, userId=currentuserid, roomId=roomId, foodId=foodId, amenitiesId=amenitiesId, checkindate=checkindate, checkoutdate=checkoutdate, dateOfBooking=datetime.now().date(), confirmation=conf, feedback="")
    food=FoodOptions.query.filter_by(id=foodId).first().type
    amenity=Amenities.query.filter_by(id=amenitiesId).first().type
    gh=GuestHouse.query.filter_by(id=ghid).first().description
    user = User.query.filter_by(id=currentuserid).first()
    type= Rooms.query.filter_by(id=roomId).first().roomtype
    db.session.add(newBooking)
    try:
        if conf == 1:
            text = "Payment id:"+res+"\nBooking id:"+str(id)+"\nStatus=Confirmed"+"\nGuest House :"+gh+"\nRoom:"+str(type)+"\nCheckIn:"+str(checkindate)+"\nCheckOut:"+str(checkoutdate)+"\nFood:"+str(food)+"\nAmenities:"+str(amenity)+"\nConfirmation:Confirmed"
        print("confirmation1")
        if conf == 0:
            text = "Payment id:"+res+"\nBooking id:"+str(id)+"\nStatus=In Queue"+"\nGuest House :"+gh+"\nRoom:"+str(type)+"\nCheckIn:"+str(checkindate)+"\nCheckOut:"+str(checkoutdate)+"\nFood:"+str(food)+"\nAmenities:"+str(amenity)+"\nConfirmation:Confirmed"
        send_confirmation_mail("Booking Confirmed", text, user.email)
        print("Booking added successfully")
        db.session.commit()
    except:
        print("Could not add new Booking to db")
    return render_template('confirm.html',paymentid=res,roomid=roomId,checkin=checkindate,checkout=checkoutdate,food=food,amenity=amenity,confirmation=conf, gh=gh, dateOfBooking=datetime.now().date())

@app.route('/cancelBooking<bookingId>', methods=["POST", "GET"])
def cancelBooking(bookingId):
    print("Cancelling")
    booking = Booking.query.filter_by(id=bookingId).first()
    money=Payment.query.filter_by(id=bookingId).first().amount
    paymentId=Payment.query.filter_by(id=bookingId).first().paymentid
    roomid = booking.roomId
    queueIds = BookingQueue.query.filter_by(id=roomId).first()
    if booking.confirmation == 0:
        tempIds = ""
        for idx in range(0, 40, 4):
            test = queueIds.bookingIds[idx:idx + 4]
            if int(str(test)) != booking.id:
                tempIds += test
        tempIds = tempIds.ljust(4, '0')
        temp=queueIds
        db.session.delete(temp)
        queueIds.bookingIds = tempIds
        db.session.add(queueIds)
        db.session.commit()
    else:
        updatestatus(roomId, booking.checkindate, booking.checkoutdate, '0')
        if queueIds is not None:
            tempIds = ""
            for idx in range(0, 40, 4):
                test = queueIds.bookingIds[idx:idx + 4]
                print(test)
                book=int(str(test))
                if checkBooking(book):
                    pass
                else:
                    tempIds += test
            if len(tempIds) < 40:
                tempIds = tempIds.ljust(4, '0')
            temp=queueIds
            db.session.delete(temp)
            queueIds.bookingIds = tempIds
            db.session.add(queueIds)
            db.session.commit()
    temp=booking
    db.session.delete(temp)
    booking.confirmation = 3
    db.session.add(booking)
    db.session.commit()
    text = "Payment id:"+paymentId+"\nBooking id:"+str(booking.id)+"\nAmount refund:"+str(money)+"\nStatus=Cancelled"
    user = User.query.filter_by(id=booking.userId).first()
    send_cancellation_mail("Booking Cancelled", text, user.email)
    if currentusertype == "Admin":
        return adminHistory()
    return history()

@app.route('/feedback/<bookingId>', methods=["POST", "GET"])
def feedback(bookingId):
    return render_template('feedback.html', bookingId=bookingId)

@app.route('/setfeedback/<bookingId>', methods=["POST", "GET"])
def setfeedback(bookingId):
    getfeedback = request.form['text']
    booking = Booking.query.filter_by(id=bookingId).first()
    temp=booking
    db.session.delete(temp)
    booking.feedback = getfeedback
    db.session.add(booking)
    db.session.commit()
    return history()

if __name__ == '__main__':
    app.run(debug = True)

