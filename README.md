
# mosquito

*mosquito* is a news aggregator which supports various types of data sources like RSS, Twitter etc. It fetches data (HTML, image, text) in parallel from sources and process that data in different manners: execute a shell script with arguments, send data to an email with custom properties (subject, priority, headers)).

### Main features:

* Work in parallel. Each configuration works in a separate process (Python [multiproccessing](https://docs.python.org/3/library/multiprocessing.html)).
* Support data sources: RSS, Twitter.
* Support for a capture of image, HTML, text from a page.
* Support regex (case insensitive) for content matching.
* Support actions (if regex was matched) for content processing.
* Support an offline mode. Save data to a database if a SMTP server is not available.
* Support update alerts and update intervals for configurations.

### Available actions:

* **execute** - execute a script with parameters  
    
  e.g. execute=/path/to/script.sh

  $1 - path to file with original content  
  $2 - path to a grabbed HTML file  
  $3 - path to a grabbed image file  
  $4 - path to a grabbed text file
  
  files created as temporary with "mosquito _" prefix in their names
  
* **grab** - grab the source of data  
    
  e.g. grab=full|html|image|text

  full - grab image, HTML, text  
  html - grab only HTML data  
  image - grab only image data  
  text - grab only text
    
  *images* are captured with help of [Selenium](http://selenium-python.readthedocs.io/) and [Firefox](https://www.mozilla.org/en-US/)  
  *html* and *text* are fetched with [Requests](http://docs.python-requests.org/en/latest/)
  
  multiple options are supported
  
* **header** - add a custom header into an email  
    
  e.g header=X-foo:bar
    
  multiple options are supported
  
* **prority** - set priority for an email  
    
  e.g. priority=high|normal|low

* **subject** - add a custom string to the email subject  
    
  e.g. subject=HelloWorld: 

### Example of configuration file:

```
[main]

# Base prefix for attachments.
attachment_name = mosquito

# Destination by default.
destination = user@example.com

# Amount of time (seconds) for an entire connection.
grab_timeout = 60

# Set custom mime type for attachements. It could be need for ELK imap plugin, for instance :)
mime = logstash

# Email settings.
smtp_server = mail.example.com
smtp_port = 25
smtp_usessl = true
smtp_auth = true
smtp_from = mosquito@example.com
smtp_username = user@example.com
smtp_password = Passw0rD

# Default length of an email subject.
subject_length = 100

# Send an alert email, if no new data during specific interval. Default value.
update_alert = 7d

# Update interval. Default value.
update_interval = 15m

# Custom "User-Agent" string.
user_agent = Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; FSL 7.0.6.01001)

# Verbosity level
verbose = info

# Twitter settings.
[twitter]

consumer_key = <CONSUMER_KEY>
consumer_secret = <CONSUMER_SECRET>
access_token_key = <ACCESS_KEY>
access_token_secret = <ACCESS_SECRET>
```

### Some examples:


Create Twitter configuration:
```
mosquito create --plugin twitter --source rianru --destination user@example.com --update-interval 1m --description 'РИА Новости' --regexp '.*' --regex-action execute=/path/to/script.sh subject=Twitter: 
```

Create RSS configuration:
```
mosquito create --plugin rss --source http://feeds.dzone.com/home --destination user@example.com --update-interval 1d --description 'DZone feeds' --regex 'javascript' --regex-action grab=text header=X-mosquito:dzone 
```

Delete all Twitter configurations:
```
mosquito delete --plugin twitter
```

Delete specific configuration:
```
mosquito delete --id 1
```

Update specific configuration:
```
mosquito set --id 1 --source http://example.com --update-interval 1w
```

Disable specific configuration:
```
mosquito set --id 1 --enabled False
```

### Output examples:

List configurations:

```
+----+---------+---------+------------------------------------------------------------------+---------------------+--------------+-----------------+-------------+--------+------------------------------------+---------------------+-------+
| ID | Enabled | Plugin  | Source                                                           | Destination         | Update alert | Update interval | Description | Regexp | Regexp action                      |     Last update     | Count |
+----+---------+---------+------------------------------------------------------------------+---------------------+--------------+-----------------+-------------+--------+------------------------------------+---------------------+-------+
| 1  |   True  | rss     | http://www.opennet.ru/opennews/opennews_all.rss                  | o.popov@livelace.ru |     7d       |       15m       |     None    | .*     | header=X-mosquito-tag1:it          | 2016-10-11 06:25:02 | 17    |
|    |         |         |                                                                  |                     |              |                 |             |        | header=X-mosquito-tag2:common      |                     |       |
|    |         |         |                                                                  |                     |              |                 |             |        | header=X-mosquito-lang:ru          |                     |       |
|    |         |         |                                                                  |                     |              |                 |             |        | grab=text                          |                     |       |
+----+---------+---------+------------------------------------------------------------------+---------------------+--------------+-----------------+-------------+--------+------------------------------------+---------------------+-------+
```

