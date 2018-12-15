import redis_utils

# check if the module is being executed
if __name__ == '__main__':
    import sys, os

    # get the db database
    if len(sys.argv) == 1:
        print("usage: python redis_init.py  [--help][--encrypt] --heroku|<database_url>")

    database_url = sys.argv[-1] if "--heroku" not in sys.argv[1:] else os.environ['REDIS_URL']
    encrypt =  True if "--encrypt" in sys.argv[1:] else False

    redis_utils.connect(database_url, encrypt)
    redis_utils.init()
    print("Database initialized!")