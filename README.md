
# mosquito

*mosquito* is a news aggregator which supports various types of data sources like RSS, Twitter etc. It fetches data (HTML, images, screenshot, text) in parallel from sources and process that data in different manners: execute a shell script with arguments, send data to an email with custom properties (subject, priority, headers)).

### Main features:

* Work in parallel. Configurations are splitted into a process pool (Python [multiproccessing](https://docs.python.org/3/library/multiprocessing.html)).
* Support data sources: RSS, Twitter.
* Support for grabbing from a web-page: HTML, images, screenshot, text.
* Support regex (case insensitive) for content matching.
* Support actions (if regex was matched) for content processing.
* Support an offline mode. Save data to a database if a SMTP server is not available.
* Support update alerts and update intervals for configurations.
* Support encoding detection and transformation (default to UTF-8).

### Available destinations:

* **exec** - execute a script with arguments  
  e.g. exec:/path/to/script.sh
  
  **$1** - a message timestamp (date a time of a publication)  
  **$2** - a comma separated list of tags  
  **$3** - path to a directory with grabbed content

  multiple options are supported

* **mail** - send an email  
  e.g. mail:user@example.com

  multiple options are supported

### Available actions:


* **grab** - grab the source of data  
    
  e.g. grab=full|html|screenshot|text

  **full** - grab image, HTML, text  
  **html** - grab only HTML data  
  **images** - grab all images which were found on a web-page  
  **screenshot** - grab only a screenshot of a web-page  
  **text** - grab only text
    
  multiple options are supported
  
* **tag** - add a custom tag for a configuration.   
    
  e.g tag=Foo:Bar
    
  multiple options are supported
  
* **prority** - set priority for an email  
    
  e.g. priority=high|normal|low

* **subject** - add a custom string to the email subject  
    
  e.g. subject=HelloWorld: 

### Example of configuration file:

```
[main]

# Email address that use for alerts
alert_email = user@example.com

# Frequency of an alert email for sources which don't have new data.
# "s" - seconds
# "m" - minutes
# "h" - hours
# "d" - days
alert_interval = 1d

# Subject for alert emails 
alert_subject = ***Mosquito: No new data ***

# Set custom mime type and name for attachments. It could be need for ELK imap plugin, for instance :)
attachment_mime = logstash
attachment_name = mosquito

# Check SSL certificates of data sources
check_ssl = True

# Destination by default.
destination = exec:/path/to/script.sh, mail:user@example.com

# Default directory where all grabbed content will be placed before exec a script
exec_path = /tmp/mosquito

# Path to a browser and a browser driver (it needs for making screenshots of web-pages).
browser_path = /usr/bin/firefox
browser_driver_path = /usr/local/bin/geckodriver

# Only specific size images will be matched/saved (grab=images).
image_min = 600x300
image_max = 800x600

# Amount of time (in seconds) for an entire connection to a data source.
grab_timeout = 60

# Process pool which will process configurations.
pool = 4

# Set defaults for regex and regex action.
regex = .*
regex_action = grab=text, subject=Mosquito:

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

# Send an alert email, if no new data during specific interval.
update_alert = 7d

# Update interval. Default value.
update_interval = 15m

# Custom "User-Agent" string.
user_agent = Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; FSL 7.0.6.01001)

# Verbosity level
log_level = info

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
mosquito create --plugin twitter --source rianru --destination mail:user@example.com --update-interval 1m --description "РИА Новости" --regex ".*" --regex-action grab=text grab=html subject=Twitter: 
```

Create RSS configuration:
```
mosquito create --plugin rss --source http://feeds.dzone.com/home --destination mail:user@example.com --update-interval 1d --description "DZone feeds" --regex "javascript" --regex-action grab=text tag=X-mosquito:dzone 
```

Delete specific configurations :
```
mosquito delete --id 1 2 3
mosquito delete --plugin twitter
```

Update specific configurations:
```
mosquito set --id 1 2 3 --source http://example.com --update-interval 1w
mosquito set --plugin rss --update-alert 1d --update-interval 1s --regex-action grab=full
```

Disable specific configuration:
```
mosquito set --id 1 2 3 --enabled False
mosquito set --plugin twitter --enabled False
```

List configurations:

```
+----+---------+---------+--------+-----------------------+-------+----------+-------------+-------+------------------+-----------------+---------------------+-------+
| ID | Enabled |  Plugin | Source | Destination           | Alert | Interval |     Desc    | Regex | Regex Action     | Images Settings | Last Update         | Count |
+----+---------+---------+--------+-----------------------+-------+----------+-------------+-------+------------------+-----------------+---------------------+-------+
| 1  |   True  | twitter | rianru | mail:user@example.com |  7d   |   1m     | РИА Новости | .*    | grab=text        |   min:600x300   | 1970-01-01 03:00:00 | 0     |
|    |         |         |        |                       |       |          |             |       | grab=html        |   max:800x600   |                     |       |
|    |         |         |        |                       |       |          |             |       | subject=Twitter: |                 |                     |       |
+----+---------+---------+--------+-----------------------+-------+----------+-------------+-------+------------------+-----------------+---------------------+-------+
```

