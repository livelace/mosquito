""" Help module """

class MosquitoHelp(object):
    
    def __init__(self):
        self.description = '''Mosquito is a news aggregator which supports 
                            various of data sources like RSS, Twitter and so on. 
                            It fetches data from source and sends  to email.'''
        self.create = 'Create a configuration'
        self.delete = 'Delete a configuration'
        self.disable = 'Disable a configuration'
        self.enable = 'Enable a configuration'
        self.list = 'List configurations'
        self.fetch = 'Fetch data from source'