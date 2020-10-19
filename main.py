from os import access
import requests
from dotmap import DotMap
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
from firebase_admin import auth
import datetime
from datetime import timedelta

# Use the application default credentials
cred = credentials.ApplicationDefault()
firebase_admin.initialize_app(cred, {
    'projectId': "trentiemeciel",
})

def from_request(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/1.0/api/#flask.Flask.make_response>`.
    """

    # Set CORS headers for preflight requests
    if request.method == 'OPTIONS':
        # Allows GET requests from origin https://mydomain.com with
        # Authorization header
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST',
            'Access-Control-Allow-Headers': 'content-type',
            'Access-Control-Max-Age': '3600',
#            'Access-Control-Allow-Credentials': 'false'
        }
        return ('', 204, headers)

    from flask import abort
    if request.method != 'POST':
        return abort(405)
    
    request_data = DotMap(request.get_json())
    accesss_token = request_data.access_token
    firebase_token = convert_auth0_token_to_firebase_token(accesss_token)
    headers = {
        'Access-Control-Allow-Origin': '*',
#        'Access-Control-Allow-Credentials': 'false'
    }
    return ({
        "firebase_token": firebase_token
    }, 200, headers)

def convert_auth0_token_to_firebase_token(auth0_token):
    # valid auth0_token and get user_profile
    up = get_user_profile(auth0_token)    
    return create_firebase_token(up)


def create_firebase_token(user_profile):
    uid = user_profile.sub
    custom_token = auth.create_custom_token(uid)
    return str(custom_token, "utf-8")


def create_session_in_firestore(access_token, user_profile):

    assert user_profile.sub is not None
    sub = user_profile.sub

    db = firestore.client()    
    auth.create_custom_token(sub)
    
    user_doc_ref = db.collection("users").document(sub)
    user_doc_ref.set(user_profile.toDict())
    session_doc_ref = db.collection(u'sessions').document(access_token)
    session_doc_ref.set({
        "expiration": datetime.datetime.now() + timedelta(days=1),
        "user": user_doc_ref
    })

def get_user_profile(token):
    headers = {
        "Authorization": f"Bearer {token}"
    }

    req = requests.get("https://30emeciel.eu.auth0.com/userinfo", headers=headers)
    req.raise_for_status()
    resp = req.json()
    return DotMap(resp)

if __name__ == "__main__":
    firebase_token = convert_auth0_token_to_firebase_token("Irsqzy4Bso-cqziWutbAYqvdanlCjCjV")
    print(f"firebase_token: {firebase_token}")