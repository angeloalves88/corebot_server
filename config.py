import os


class Config:
    TENANT_ID = 1111
    TENANT_NAME = 'DAFE-DEMO'
    CUSTOMER_KEY = ""

    SQLALCHEMY_DATABASE_URI = "mysql+pymysql://adminmysql:sQHJFQ3hBzA44O13cQoE_@easypanel.promotionsgroup.website/corebotpy_demo"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SECRET_KEY = os.urandom(24)

    QUEUE_PROVIDER = "CLOUDAMQP_URL"
    QUEUE_CONNECT = "amqps://jexvvaep:QX58STt78M_LMSPNbTmd3tWvg3Y_IBdO@jaragua.lmq.cloudamqp.com/jexvvaep"
