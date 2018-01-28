class MosquitoHelp(object):
    
    def __init__(self):
        self.description = """Mosquito is a news aggregator which supports various types of data sources like RSS, 
        Twitter etc. It fetches data (HTML, image, text) in parallel from sources and process that data in 
        different manners: execute a shell script with arguments, send data to an email with custom properties 
        (subject, priority, headers)).
        """
        self.create1 = "Create a configuration"
        self.create2 = "Set a plugin name for a source (rss, twitter)"
        self.create3 = "Set an URL for RSS or a channel name for Twitter"
        self.create4 = "Set a space separated list of email addresses"
        self.create5 = "Set an update alert interval (1s, 2m, 3h, 4d)"
        self.create6 = "Set an update interval (1s, 2m, 3h, 4d)"
        self.create7 = "Set description text"
        self.create8 = "Set a space separated list of regexs (only matched messages will be process)"
        self.create9 = "Set a space separated list of actions (see documentation for details)"

        self.delete1 = "Delete configurations"
        self.delete2 = "Set a space separated list of plugins"
        self.delete3 = "Set a space separated list of IDs"

        self.fetch1 = "Fetch data from a source"
        self.fetch2 = "Set a space separated list of plugins"
        self.fetch3 = "Set a space separated list of IDs"
        self.fetch4 = "Force operation (will process disabled configurations and ignore an update interval)"

        self.list1 = "List configurations"
        self.list2 = "Set a space separated list of plugins"
        self.list3 = "Set a space separated list of IDs"

        self.set1 = "Set parameters for configurations"
        self.set2 = "Set status of a configuration (True or False)"
        self.set3 = "Set a space separated list of IDs"
        self.set4 = "Set a space separated list of plugins"
        self.set5 = "Set an URL for RSS or a channel name for Twitter"
        self.set6 = "Set a space separated list of email addresses"
        self.set7 = "Set an update alert interval (1s, 2m, 3h, 4d)"
        self.set8 = "Set an update interval (1s, 2m, 3h, 4d)"
        self.set9 = "Set description text"
        self.set10 = "Set a space separated list of regexs (only matched messages will be process)"
        self.set11 = "Set a space separated list of actions (see documentation for details)"


