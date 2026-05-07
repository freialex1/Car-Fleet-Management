from flask import Flask ,Response,request,render_template,redirect,session, url_for,jsonify
import pymongo
import json
import os
from user import User
app = Flask(__name__)
app.static_folder = 'static'
from bson.objectid import ObjectId
from cars import Cars
from werkzeug.utils import secure_filename
from datetime import datetime
from pymongo import MongoClient


##################################### MOHAMED FATEHI #########################################

## CONNECTION TO DB
try : 
    mongo = pymongo.MongoClient(host="localhost", port =27017,serverSelectionTimeoutMS =1000 )
    db = mongo.location_voitures #use the company db in mongo 
    mongo.server_info() 
    print("connect to db")

except : 
    print("ERROR - Cannot connect to db")


#ROOT TO LOGIN
@app.route("/login")
def blade() : 
    return render_template("login.html")


#AUTHENTIFICATION 

@app.route("/auth", methods=["POST"])
def auth():
    email = request.form["email"]
    password = request.form["password"]
    session['email'] = email
  
    
    user = User.authenticate(email, password)
  

    if user is not None:
        # Authentication successful, redirect to get_cars route
        return redirect(url_for('get_cars'))

    return render_template("login.html", error_message="Invalid credentials")




#GET ALL THE CARS BASED ON THE ETAT 
@app.route('/cars', methods=['GET'])
def get_cars():
 email = session.get('email')

 car_list = Cars.get()
 user = User.get(email)
 return render_template('category.html', cars=car_list,user=user)

@app.route('/logout')
def logout():
    session.clear()
    return render_template('login.html')



@app.route('/addManager' ,methods=['POST','GET'])
def addManager():
    if request.method == 'POST':
        client_data = {
            'password': request.form['password'],
            'nom': request.form['nom'],
            'prenom': request.form['prenom'],
            'email': request.form['email'],
            'tel': request.form['telephone'],
            'ville': request.form['ville'],
            'role' : "manager"
        }
        db.utilisateur.insert_one(client_data)
        session['success'] = True
        return redirect('/manager')
        #return render_template('ManagerList.html',success_message="Manager bien saisie!")
    return render_template('addManager.html') 




@app.route('/addAdmin' ,methods=['POST','GET'])
def addAdmin():
    if request.method == 'POST':
        client_data = {
            'password': request.form['password'],
            'nom': request.form['nom'],
            'prenom': request.form['prenom'],
            'email': request.form['email'],
            'tel': request.form['telephone'],
            'ville': request.form['ville'],
            'role' : "admin"
        }
        db.utilisateur.insert_one(client_data)
        session['success'] = True
        return render_template('addAdmin.html',success_message="Admin bien saisie!")
    return render_template('addAdmin.html')
    
@app.route('/manager')
def list_managers():
    role = "manager"
    managers = db.utilisateur.find({'role': role})
    return render_template('ManagerList.html', clients=managers)


@app.route('/deleteManager', methods=['POST'])
def delete_manager():

    manager_id = ObjectId(request.form.get('idClient'))
    print(manager_id)

    print(f"Deleting client with ID: {manager_id}")


    result = db.utilisateur.delete_one({'_id': manager_id})

    if result.deleted_count > 0:
        return redirect(url_for('list_managers'))
    else:
        return 'Failed to delete the client or client not found.'
    
    
@app.route('/admin')
def list_admins():
    role = "admin"
    managers = db.utilisateur.find({'role': role})
    return render_template('AdminList.html', clients=managers)


@app.route('/deleteAdmin', methods=['POST'])
def delete_admin():

    manager_id = ObjectId(request.form.get('idClient'))
    print(manager_id)

    print(f"Deleting client with ID: {manager_id}")


    result = db.utilisateur.delete_one({'_id': manager_id})

    if result.deleted_count > 0:
        return redirect(url_for('list_admins'))
    else:
        return 'Failed to delete the client or client not found.'


@app.route('/modify_manager', methods=['POST'])
def modify_manager():

    print(request.form)  # Debugging line
    id= ObjectId(request.form['CIN'])
    nom = request.form['nom']
    prenom = request.form['prenom']
    email = request.form['email']
    telephone = request.form['telephone']
    ville= request.form['ville']

    # Find the client with the matching CIN
    query = {'_id': id}
    client = db.utilisateur.find_one(query)

    if client:
        # Update the client data
        update = {
            '$set': {
                'nom': nom,
                'prenom': prenom,
                'email': email,
                'tel': telephone,
                'ville': ville
            }
        }
        db.utilisateur.update_one(query, update)

        return redirect(url_for('list_managers'))
    else:
        return 'Manager not found'


  
@app.route('/modify_admin', methods=['POST'])
def modify_admin():

    print(request.form)  # Debugging line
    id= ObjectId(request.form['CIN'])
    nom = request.form['nom']
    prenom = request.form['prenom']
    email = request.form['email']
    telephone = request.form['telephone']
    ville= request.form['ville']

    # Find the client with the matching CIN
    query = {'_id': id}
    client = db.utilisateur.find_one(query)

    if client:
        # Update the client data
        update = {
            '$set': {
                'nom': nom,
                'prenom': prenom,
                'email': email,
                'tel': telephone,
                'ville': ville
            }
        }
        db.utilisateur.update_one(query, update)

        return redirect(url_for('list_admins'))
    else:
        return 'Admin not found'






##############################""ANAS#######################



# Connect to MongoDB
try:
    mongo = pymongo.MongoClient(
        host='localhost', 
        port=27017,
        serverSelectionTimeoutMS = 1000     
    )

    db = mongo.location_voitures
    cars_collection = db['voiture']
    mongo.server_info() # trigger exception if cannot connect to db
    print("Connected to db")
except:
    print("ERROR - Cannot connect to db")

def predict_service(car_id, service_type="oil"):
    car_id_str = str(car_id)

    if service_type == "major":
        service_names = ["nagyszerviz", "major"]
        default_interval = 60000
    else:
        service_names = ["olajcsere", "oil"]
        default_interval = 10000

    last_service = db['maintenance'].find_one(
        {
            "car_id": car_id_str,
            "type": {"$in": service_names}
        },
        sort=[("_id", -1)]
    )

    if last_service and last_service.get("date"):
        usages = list(db['daily_usage'].find({
            "car_id": car_id_str,
            "date": {"$gt": last_service.get("date")}
        }))
    else:
        usages = list(db['daily_usage'].find({"car_id": car_id_str}))

    if not usages:
        return {
            "avg_km_per_day": 0,
            "total_km": 0,
            "remaining_km": default_interval,
            "days_estimate": "N/A",
            "status": "nincs futásadat",
            "interval": default_interval
        }

    total_km = 0

    usage_weights = {
        "city": 0.7,
        "mixed": 1.0,
        "highway": 1.2,
        "intensive": 0.6
    }

    total_weight = 0
    count = 0

    for u in usages:
        try:
            total_km += int(u.get("km_driven", 0))
        except:
            pass

        usage = u.get("usage_type", "mixed")
        total_weight += usage_weights.get(usage, 1.0)
        count += 1

    avg_km_per_day = total_km / count if count > 0 else 0
    avg_weight = total_weight / count if count > 0 else 1.0

    interval = int(default_interval * avg_weight)
    remaining_km = interval - total_km

    if avg_km_per_day > 0:
        days_estimate = int(remaining_km / avg_km_per_day)
    else:
        days_estimate = "N/A"

    if remaining_km <= 0:
        status = "lejárt"
    elif service_type == "major":
        if days_estimate == "N/A":
            status = "ismeretlen"
        elif days_estimate > 180:
            status = "rendben"
        elif 60 < days_estimate <= 180:
            status = "hamarosan"
        else:
            status = "sürgős"
    else:
        if days_estimate == "N/A":
            status = "ismeretlen"
        elif days_estimate > 30:
            status = "rendben"
        elif 10 < days_estimate <= 30:
            status = "hamarosan"
        else:
            status = "sürgős"

    return {
        "avg_km_per_day": round(avg_km_per_day, 1),
        "total_km": total_km,
        "remaining_km": remaining_km,
        "days_estimate": days_estimate,
        "status": status,
        "interval": interval
    }

@app.route('/manage_cars')
def manage_cars():
    cars = list(cars_collection.find())
    car_count = len(cars)
    return render_template('managecars.html', cars=cars, car_count=car_count)

UPLOAD_FOLDER = 'static/images/cars/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/add_car', methods=['GET', 'POST'])
def add_car():
    if request.method == 'POST':
        make = request.form['make']
        model = request.form['model']
        year = int(request.form['year'])
        price = int(request.form['price'])
        matricule = request.form['matricule']
        image = request.files['image']

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)

            car_data = {
                'marque': make,
                'modele': model,
                'annee': year,
                'prix': price,
                'matricule': matricule,
                'image': filename
            }
            cars_collection.insert_one(car_data)

            return redirect('/manage_cars')

    return render_template('addcar.html')


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/update_car', methods=['POST'])
def update_car():
    car_id = request.form.get('carId')
    make = request.form['make']
    model = request.form['model']
    year = int(request.form['year'])
    price = int(request.form['price'])
    matricule = request.form['matricule']

    filter_criteria = {'_id': ObjectId(car_id)}
    update_data = {'$set': {'marque': make, 'modele': model, 'annee': year, 'prix': price, 'matricule': matricule}}

    try:
        cars_collection.update_one(filter_criteria, update_data)
        return redirect('/manage_cars')
    except Exception as e:
        print(f"Error updating document: {e}")


@app.route('/modify_car')
def modify_car():
    car_id = request.args.get('carId')
    car = cars_collection.find_one({'_id': ObjectId(car_id)})

    if car:
        return render_template('modifycar.html', car=car)
    else:
        return "Car not found"

@app.route('/delete_car', methods=['POST'])
def delete_car():
    car_id = request.form.get('carId')

    try:
        cars_collection.delete_one({'_id': ObjectId(car_id)})
        return redirect('/manage_cars')
    except Exception as e:
        print(f"Error deleting document: {e}")


@app.route('/add_maintenance', methods=['GET', 'POST'])
def add_maintenance():
    if request.method == 'POST':
        car_id = request.form['car_id']
        type_ = request.form['type']
        current_km = request.form['current_km']
        cost = request.form['cost']
        description = request.form['description']
        date = request.form['date']

        partner_id = request.form['partner_id']

        partner = db['partners'].find_one({
            '_id': ObjectId(partner_id)
        })

        partner_name = partner.get('name') if partner else ''

        car = cars_collection.find_one({
            '_id': ObjectId(car_id)
        })

        matricule = car.get('matricule') if car else ''

        maintenance_data = {
            "car_id": car_id,
            "matricule": matricule,
            "type": type_,
            "current_km": current_km,
            "partner_id": partner_id,
            "partner_name": partner_name,
            "cost": cost,
            "description": description,
            "date": date
        }

        db['maintenance'].insert_one(maintenance_data)

        return redirect('/maintenance')

    cars = list(cars_collection.find())
    partners = list(db['partners'].find())

    return render_template(
        'addmaintenance.html',
        cars=cars,
        partners=partners
    )


@app.route('/maintenance')
def maintenance_list():
    maintenances = list(db['maintenance'].find())

    for m in maintenances:
        prediction = predict_service(m["car_id"])
        m["prediction"] = prediction

    return render_template('maintenance.html', maintenances=maintenances)
    
    
@app.route('/add_daily_usage', methods=['GET', 'POST'])
def add_daily_usage():
    if request.method == 'POST':
        car_id = request.form['car_id']
        date = request.form['date']
        km_driven = request.form['km_driven']
        usage_type = request.form['usage_type']
        description = request.form['description']

        car = cars_collection.find_one({'_id': ObjectId(car_id)})
        matricule = car.get('matricule') if car else ''

        daily_usage_data = {
            "car_id": car_id,
            "matricule": matricule,
            "date": date,
            "km_driven": km_driven,
            "usage_type": usage_type,
            "description": description
        }

        db['daily_usage'].insert_one(daily_usage_data)

        return redirect('/manage_cars')

    cars = list(cars_collection.find())
    return render_template('adddailyusage.html', cars=cars)
    
@app.route('/daily_usage')
def daily_usage_list():
    daily_usages = list(db['daily_usage'].find())
    return render_template('dailyusage.html', daily_usages=daily_usages)
    
    
@app.route('/car_status')
def car_status():
    cars = list(cars_collection.find())

    result = []
    alerts = []

    for car in cars:
        oil_prediction = predict_service(car["_id"], "oil")
        major_prediction = predict_service(car["_id"], "major")

        item = {
            "car": car,
            "oil_prediction": oil_prediction,
            "major_prediction": major_prediction
        }

        result.append(item)

        # ⚠️ ALERT LOGIKA
        if oil_prediction["status"] != "rendben":
            alerts.append({
                "car": car,
                "type": "Olajcsere",
                "status": oil_prediction["status"]
            })

        if major_prediction["status"] != "rendben":
            alerts.append({
                "car": car,
                "type": "Nagyszerviz",
                "status": major_prediction["status"]
            })

    return render_template('carstatus.html', data=result, alerts=alerts)
    
    
@app.route('/add_partner', methods=['GET', 'POST'])
def add_partner():
    if request.method == 'POST':
        partner_data = {
            "name": request.form['name'],
            "type": request.form['type'],
            "phone": request.form['phone'],
            "email": request.form['email'],
            "address": request.form['address'],
            "contact_person": request.form['contact_person'],
            "note": request.form['note']
        }

        db['partners'].insert_one(partner_data)

        return redirect('/partners')

    return render_template('addpartner.html')
    
    
@app.route('/partners')
def partners_list():
    partners = list(db['partners'].find())
    return render_template('partners.html', partners=partners)


@app.route('/delete_partner', methods=['POST'])
def delete_partner():
    partner_id = request.form['partner_id']
    db['partners'].delete_one({'_id': ObjectId(partner_id)})
    return redirect('/partners')

############################ AHMED ##################################

app.secret_key = 'HereWegoAgain'


client = MongoClient('mongodb://localhost:27017')
db = client['location_voitures']
collection = db['client']


@app.route('/AddNewClient')
def hello():
    return render_template('AddNewClient.html')

@app.route('/add_client', methods=['POST'])
def add_client():
    client_data = {
        'cin': request.form['CIN'],
        'nom': request.form['nom'],
        'prenom': request.form['prenom'],
        'email': request.form['email'],
        'tel': request.form['telephone'],
        'adresse': request.form['adresse']
    }
    collection.insert_one(client_data)

    session['success'] = True

    return redirect(url_for('list_clients'))


@app.route('/clients')
def list_clients():
    clients = collection.find()
    return render_template('ClientList.html', clients=clients, client=None)





@app.route('/deleteClient', methods=['POST'])
def delete_client():

    client_id = request.form.get('idClient')

    print(f"Deleting client with ID: {client_id}")


    result = collection.delete_one({'cin': client_id})

    if result.deleted_count > 0:
        return redirect(url_for('list_clients'))
    else:
        return 'Failed to delete the client or client not found.'
    





@app.route('/add_new_client')
def add_new_client():
    success = session.pop('success', False)
    if success:
        return """
        <script>
            Swal.fire({
                title: 'Success!',
                text: 'Client data inserted successfully.',
                icon: 'success',
                confirmButtonText: 'OK'
            });
        </script>
        """

    return render_template('AddNewClient.html')
@app.route('/modify_client', methods=['POST'])
def modify_client():

    print(request.form)  # Debugging line
    cin = request.form['CIN']
    nom = request.form['nom']
    prenom = request.form['prenom']
    email = request.form['email']
    telephone = request.form['telephone']
    adresse = request.form['adresse']

    # Find the client with the matching CIN
    query = {'cin': cin}
    client = collection.find_one(query)

    if client:
        # Update the client data
        update = {
            '$set': {
                'nom': nom,
                'prenom': prenom,
                'email': email,
                'tel': telephone,
                'adresse': adresse
            }
        }
        collection.update_one(query, update)

        return redirect(url_for('list_clients'))
    else:
        return 'Client not found'






############################### MOUAD ###################################
reservation_collection = db['reservation']

@app.route("/location_car/<voiture_id>", methods=['GET', 'POST'])
def location_car(voiture_id):
    if request.method == 'POST':
        client_id = ObjectId(request.form.get('client'))
        voiture_id = ObjectId(voiture_id)
        date_debut_str = request.form.get('date_debut')
        date_fin_str = request.form.get('date_fin')
        
        voitures = db.voiture.find_one({"_id": ObjectId(voiture_id)})
        date_debut = datetime.strptime(date_debut_str, "%Y-%m-%d")
        date_fin = datetime.strptime(date_fin_str, "%Y-%m-%d")

        # Calculate the difference in days
        diff_days = (date_fin - date_debut).days

        # Calculate the price based on the difference in days
        price = diff_days * voitures.get('prix')
        print(price)
        
        
        #prix_reservation = int(request.form.get('prix_reservation'))
        statut = request.form.get('statut', 'en_attente')  # Set the default value to "en_attente"

        # Convert date_debut and date_fin to datetime objects
        date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d')
        date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d')

        print("====================================")
        print(client_id)
        print(voiture_id)
        print(date_debut)
        print(date_fin)
        print(statut)
        print("====================================")

        # Store the client, car, and statut details in the reservation collection
        reservation = {
            'client_id': client_id,
            'voiture_id': voiture_id,
            'date_debut': date_debut,
            'date_fin': date_fin,
            'prix_reservation': price,
            'statut': statut
        }
        reservation_collection.insert_one(reservation)
        clients = db['client'].find()

        # Redirect or render a success page
        return redirect('/cars')
        #return render_template('location_car.html',success_message="Voiture bien reserver!",clients=clients, voiture_id=voiture_id,voiture=voitures)

    # Fetch client and car data to populate the select options
    clients = db['client'].find()
  
    voitures = db.voiture.find_one({"_id": ObjectId(voiture_id)})
    
   

  
    return render_template("location_car.html", clients=clients, voiture_id=voiture_id,voiture=voitures)















# Route to display all reservations and handle accept/refuse functionality
@app.route('/gestion_reservations', methods=['GET', 'POST'])
def gestion_reservations():
    if request.method == 'POST':
        reservation_id = request.form.get('reservation_id')  # Get the reservation ID from the submitted form
        action = request.form.get('action')  # Get the action (accept/refuse) from the submitted form
        
        print(reservation_id, action)
        
        # Update the reservation status based on the action
        reservation_collection.update_one({'_id': ObjectId(reservation_id)}, {'$set': {'statut': action}})
        
        # return 'Reservation updated successfully!'
    
            
    # Fetch all reservations from the collection
    reservations = reservation_collection.find({"statut": "en_attente"})

    return render_template('gestion_reservations.html', reservations=reservations)




# Route to edit a reservation
@app.route('/edit_reservation/<reservation_id>', methods=['GET', 'POST'])
def edit_reservation(reservation_id):
    # Retrieve the reservation object using reservation_id (example implementation)
    reservation = db.reservations.find_one({'_id': ObjectId(reservation_id)})
    print(reservation_id, reservation.get('client_id'))

    return render_template('edit_reservation.html', reservation=reservation)


# Route to dashboard
@app.route('/dashboardTest')
def dashboardtest():
    # Fetch all reservations from the collection
    reservations = list(reservation_collection.find())
    client_collection = db['client']
    
    
    # Fetch all clients from the collection
    clients = list(client_collection.find())
    
    # Extract the status counts from reservations
    status_counts = {}
    for reservation in reservations:
        status = reservation.get('statut')
        if status:
            status_counts[status] = status_counts.get(status, 0) + 1
            
            



    # Extract the address counts from clients
    address_counts = {}
    for client in clients:
        address = client.get('adresse')
        if address:
            address_counts[address] = address_counts.get(address, 0) + 1

    
    # Prepare the data for the chart
    labels = list(status_counts.keys())
    data = list(status_counts.values())



    # Prepare the data for the chart
    labels1 = list(address_counts.keys())
    data1 = list(address_counts.values())
    
    
    
    return render_template('dashboard_test.html', 
                           labels=json.dumps(labels), 
                           data=json.dumps(data),
                           labels1=json.dumps(labels1), 
                           data1=json.dumps(data1)
                           )











####################################
# if the script is the main programme, else if its imported from another module not __main__
if __name__ == "__main__"  :
    app.run(port =80, debug =True ) 





