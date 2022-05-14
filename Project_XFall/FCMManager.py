import firebase_admin 
from firebase_admin import credentials, messaging
from XFall import settings

cred = credentials.Certificate(settings.CRED)
firebase_admin.initialize_app(cred)

def pushNotif (title, message, regis_token, dataObject=None):
    message = messaging.MulticastMessage (
        notification = messaging.Notification(
            title=title, 
            body=message,),
        data=dataObject,
        tokens=regis_token
    )

    response = messaging.send_multicast(message)
    print('Success!', response)
