""" Help module """

class MosquitoHelp(object):
    
    def __init__(self):
        self.description = '''Mosquito is a news aggregator which supports 
                            various of data sources like RSS, Twitter and so on. 
                            It fetches data from source and sends  to email.'''
        self.create = 'Create a configuration'
        self.delete = 'Delete a configuration'
        self.fetch = 'Fetch data from source'
        self.list = 'List configurations'
        self.set = 'Set parameters for a configuration'