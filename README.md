
# mosquito

*mosquito* is a news aggregator which supports various of data sources like RSS, Twitter and so on. It fetches data from news source and sends this data to email.  

### Main features:

* Support as data source: RSS, Twitter.
* Support regexp for content filtering.
* Support regexp actions for content processing.

### Available actions:

* execute - execute a script with parameters
  e.g. exectute=/path/to/script.sh
  $1 - path to file with original content
  $2 - path to file with expanded text content
  $3 - path to file with expanded image content
  
* grab - grab the source of data
  e.g. grab=full|image|text
  full - grab image and text
  image - grab only image
  text - grab only text
  
* header - add a custom header into an email
  e.g header=X-foo:bar
  
* prority - set priority for an email
  e.g. priority=high|normal|low

* subject - add a custom string to the email subject
  e.g. subject=HelloWorld: 

Some examples:

```
msquito create --plugin twitter --source rianru --destination user@example.com --update-interval 1m --description 'РИА Новости' --regexp '.*' --regexp-action execute=/path/to/script.sh subject=Twitter: 
```

```
msquito create --plugin rss --source http://feeds.dzone.com/home --destination user@example.com --update-interval 1d --description 'DZone feeds' --regexp 'javascript' --regexp-action grab=text header=X-mosquito:dzone 
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
