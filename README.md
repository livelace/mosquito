
# mosquito

*mosquito* is a news aggregator which supports various of data sources like RSS, Twitter and so on. It fetches data from news source and sends this data to email.  

### Main features:

* Support as data source: RSS, Twitter.
* Support regexp for content filtering.
* Support regexp actions for content processing.
* Support for offline mode. Save data to database if a SMTP server is not reachable.

### Available actions:

* **execute** - execute a script with parameters  
    
  e.g. exectute=/path/to/script.sh  
  $1 - path to file with original content  
  $2 - path to file with expanded text content  
  $3 - path to file with expanded image content
  
  files created as temporary with "mosquito _" prefix
  
* **grab** - grab the source of data  
    
  e.g. grab=full|image|text  
  full - grab image and text  
  image - grab only image  
  text - grab only text
    
  images are captured with [PhantomJS](http://phantomjs.org/)  
  text is fetched with [Requests](http://docs.python-requests.org/en/latest/)
  
* **header** - add a custom header into an email  
    
  e.g header=X-foo:bar
    
  only one header at the moment
  
* **prority** - set priority for an email  
    
  e.g. priority=high|normal|low

* **subject** - add a custom string to the email subject  
    
  e.g. subject=HelloWorld: 
    
  base subject assembled from first 100 characters of an original content

Some examples:

```
mosquito create --plugin twitter --source rianru --destination user@example.com --update-interval 1m --description 'РИА Новости' --regexp '.*' --regexp-action execute=/path/to/script.sh subject=Twitter: 
```

```
mosquito create --plugin rss --source http://feeds.dzone.com/home --destination user@example.com --update-interval 1d --description 'DZone feeds' --regexp 'javascript' --regexp-action grab=text header=X-mosquito:dzone 
```

### Example of configuration file:

```
[main]

grab_timeout = 60

smtp_server = mail.example.com
smtp_port = 25
smtp_usessl = true
smtp_auth = true
smtp_from = mosquito@example.com
smtp_username = user@example.com
smtp_password = Passw0rD

verbose = info

[twitter]

consumer_key = <CONSUMER_KEY>
consumer_secret = <CONSUMER_SECRET>
access_token_key = <ACCESS_KEY>
access_token_secret = <ACCESS_SECRET>

```
