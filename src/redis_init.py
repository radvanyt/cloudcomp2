import redis_utils

def redis_init(database_url):
    redis_utils.connect(database_url)
    redis_utils.init()
    print("Database initialized!")


#===============================================================================
# check if the module is being executed
if __name__ == '__main__': 
    import sys, os

    # get the db database
    if len(sys.argv) != 2:
        print("usage: python redis_init.py --heroku|<database_url>")
    
    if "--heroku" in sys.argv[1]:
        database_url = os.environ['REDIS_URL']
    else:
        database_url = sys.argv[1]
        redis_init(database_url)