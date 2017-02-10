# Please note: This code is no longer in use by the RG, see: registerguard/rssonpublish [private] for new code

# TweetTweet

#### Please note this is the first draft and has not been edited yet. Sorry for typos, rambling, etc.

In brief, this is a script that takes an RSS feed of stories, runs a link through [bit.ly](http://bit.ly) and then tweets out the headline and bit.ly link when the RSS feed is updated.

For various reasons, we have it set up to run on a cron every other minute, however, if you have a hook in your CMS to trigger scripts when a story is published you could configure this to run on those events.

## Table of contents

* [Getting started](#getting-started)
  * [Assumptions](#assumptions)
  * [Dependancies](#dependancies)
  * [Directory structure](#directory-structure)
* [Code walkthrough](#code-walkthrough)
  * [Tweepy](#tweepy)
  * [bitly_api](#bitly_api)
  * [Notes](#notes)
* [Cron](#cron)
* [TL;DR](#tldr)

## Getting started

### Assumptions

* You are familiar with Python and you have pip installed
  * I have this running on Python 2.7.6, haven't tried 3
* I did all of this on a Mac, no promises for PC users
* You have a properly formatted RSS feed of content to use
* Each story has a headline, url and unique ID (url could work)
* You have bit.ly and Twitter accounts

### Dependancies

Included in the Python Standard Library

* [logging](https://docs.python.org/2/library/logging.html)
* [logging.handlers](https://docs.python.org/2/library/logging.handlers.html)
* [urllib2](https://docs.python.org/2/library/urllib2.html)
* [socket](https://docs.python.org/2/library/socket.html)

Need to be installed

* [feedparser](https://github.com/kurtmckee/feedparser) - `pip install feeparser`
* [tweepy](https://github.com/tweepy/tweepy) - `pip install tweepy`
* [bitly_api](https://github.com/bitly/bitly-api-python) - `pip install bitly_api`

### Directory structure

Here is my suggested directory structure:

```python
- tweet.py          # script
- tweet.txt         # old ID list
- logs              # logs folder
|- tweet.log        # most recent logs
|- tweet.log.1      # next most recent logs
|- ...
|- tweet.log.5      # oldest logs
```

You must create tweet.txt as the current script will not create that. I believe `open('tweet.txt', 'w+')` will do this but I have not tested it.

## Code walkthrough

Please follow along with the code as I talk through it.

Ok, so we import everything.

Set up a path to log to. I made it absolute, you don't have to. Not really sure what the `__name__` is, I borrowed this bit from a script @jheasly had. Set the level to debug. and set the formatting. Below is an example of this formatting.

![screen shot 2015-05-13 at 12 43 41 pm](https://cloud.githubusercontent.com/assets/4853944/7619470/c049f166-f96d-11e4-89db-27c7c49d6d75.png)

The `logging.handlers.RotatingFileHandler()` line keeps logs under control so that logs don't pile up over time. I have it set to create five back up files, in addition to the initial one, with a max of 256kb each. This means that as the first log file, tweet.log, fills up it saves that file as tweet.log.1 and makes a new file called tweet.log and starts filling that up. This happens up through tweet.log.5 so you will have a fair amount of logs if it breaks.

Logging does allow you to print out the console if you would like but I prefer to not do that for two reasons. First, if you forget to comment it out and set it to run on a cron (more on that later) you will start to pile up Mail files. While these are easy to get rid of (`$ mail` then `$mail delete *` then `$mail q`) I prefer to avoid Mail all together. The second reason is that you can run a `tail -f PATH/TO/LOG/FILE` and that will print print out the log file as it runs to the console by following it, that's the `-f` part. The added bonus to this is that it's all getting saved to the file so you can go look at this later if needed. The added added bonus is that you don't have any `print` statements to deal with.

Moving on, we have our first log which is just a visual cue that the script is starting. It's verbose and probably not needed in the final product.

Now we set the url of your RSS feed.

Then we try to get it with a time out of 30 seconds. If your server is getting hammered and it takes longer than 30 seconds it will error out. The socket thing is for when there is a secondary exception that urllib2 doesn't handle. Read more on that [here](http://heyman.info/2010/apr/22/python-urllib2-timeout-issue/).

Now we use urllib2 to get the response and read the html.

Now into Feedparser we parse the html and that sets an object called `entries`. That looks like this mess:

![screen shot 2015-05-13 at 12 57 12 pm](https://cloud.githubusercontent.com/assets/4853944/7619746/a0631e48-f96f-11e4-8d50-b7780c7b3c5a.png)

The above image is just one story. The important parts we want are the id, link and title.

Those can be accessed at `feed.entries[i].title` where i is the story count. But more on that later.

Now we test to see if there are any feed.entries. If there are no stories in the RSS feed then we don't want to do anything. We're about to get into some nested conditionals and loops. This is the highest level.

Just to be clear here is some pseudo code:

```python
if there are stories:
    go do stuff
else:
    log that there are "No entries"
```

Now we need to deal with checking the unique IDs. For the Guard we have unique story IDs coming from the CMS. Every CMS should have some sort of unique ID or string system to keep stories straight. URLs could also work as the unique ID but our IDs were shorter so I went with them.

So we set up an empty Python list. Then we fill it in with a for loop over the RSS data. So `id_list` is the new, incoming IDs.

Now we try and open a text file of the old IDs. The first time you run this you'll get an error (I think) if you haven't already created the tweet.txt file. Also, the first time you run this it will say, hey, you don't have any IDs, let me go ahead and tweet **every** story in your RSS. If there are a lot of stories that is a lot of tweets so I recommend commenting out the `api.update_status(status=tweet_text)` line before running it.

Then we set a new variable `loop` to zero. Now we enter into a new loop. For every ID in the list of new IDs do the following.

Then, check and see if the new ID is **not** in the old ID list. If the new ID is **not** in the new ID list then we need to tweet it because it's a new story.

The else part of this if statement says to do nothing, because the ID is not new since it is already in the file.

Let's take a step back and look at the pseudo code.

```python
if there are stories:
    for each ID in the feed:
        if the ID is NOT in the old ID list:
            go do stuff
        else:
            log that the ID is already in the file
else:
    log that there are "No entries"
```

But enough of that nonsense, let's jump back into the if part because we want to do stuff with the new ID.

Set title and URL variables.

#### [Tweepy](http://tweepy.readthedocs.org/en/v3.3.0/getting_started.html)

So now we set stuff up to deal with the Twitter API. If you haven't worked with the Twitter API before you should know that there are different clients for different languages and Tweepy is only one of the one's available for Python.

To use the Twitter API you have to provide Tweepy with credentials so that it can authenticate you. Those need to be acquired directly from Twitter.

To get those, go to [apps.twitter.com](https://apps.twitter.com) and Create New App. Access level should be Read and Write. Then you need to generate tokens.

You need four pieces of information from Twitter to authenticate. Those are Consumer Key, Consumer Secret, Access Token and Access Token Secret. The blurry parts in the image below are the things that you need.

![screen shot 2015-05-13 at 1 32 24 pm](https://cloud.githubusercontent.com/assets/4853944/7620455/d9e8a7a0-f974-11e4-8d86-d0e36a2da2ef.png)

Plug those credentials in and you're good to go on Tweepy.

#### [bitly_api](http://dev.bitly.com/index.html)

You also need to authenticate the bit.ly api. If you go [bitly.com/a/create_oauth_app](https://bitly.com/a/create_oauth_app) you can get an Access Token. Plug that in and you should be good to go on bit.ly.

Note: If you use a custom domain then you don't need to do anything special as long as it is set to your default domain. You can check this by going under your account's settings and looking for "Default short domain for your Bitlinks is set to". Consult the [bitly_api docs](http://dev.bitly.com/domains.html) if you need more info.

Now we try to go get the short link by passing it the long link. If it succeeds we get an object and we grab the url value and set that to "shorturl". If it fails, then we fall back to the long url. This way, you'll still tweet a valid url, it just won't be short.

Now, the good stuff. We set the "tweet_text" variable to the title and link.

We try to access the Twitter API and post the status. If that doesn't work we log error messages.

Now we close out of that big if statement.

We add one to the loop variable as we loop through the new url list.

Close out of that loop and we overwrite file with our new ID list so that it gets updated.

And that's about it.

### Notes

* There are better ways to utilize logging besides just logger.dubug(). Please take a look at [any](http://docs.python-guide.org/en/latest/writing/logging/) [of](http://victorlin.me/posts/2012/08/26/good-logging-practice-in-python) [these](https://docs.python.org/2/library/logging.html) to get a sense of how this can be improved from my method.
* There are certainly better ways to encapsulate bits of this code. Future versions will include methods.
* Tweepy does much more than just send tweets. Check them out for more cool things.
* I'm sure some of the things I'm doing are super inefficient but it works. Please [shoot me a note](mailto:rob.denton@registerguard.com) with tips or do a pull request or whatevs.

## Cron

Once you have a script that does what you want, you need a way to run it.

If you have a flexible CMS that can call the script whenever a story gets published that is the best possible way.

Unfortunately, that's not an option for me so I set up a cron to run every other minute.

A cron job is essentially a way to schedule something to happen on a console. You give it a time and day and it does what you tell it to. In our case we want to say every other minute run this python script.

The syntax I use is this:

`*/2	*	*	*	*	python tweet.py`

For more on crons check out [this tutorial](http://code.tutsplus.com/tutorials/scheduling-tasks-with-cron-jobs--net-8800).

If you're interested in the RG's cron machine see [here](https://github.com/registerguard/tracker/wiki/Accessing-Wave,-the-cron-machine) (private).

## TL;DR

```
get RSS feed
parse RSS feed
if there are new stories:
    for each new story ID:
        if the new ID is NOT in the old ID list:
            convert the long link to a short link
            tweet the headline and link
        else:
            log that the ID is already in the file
    overwrite old IDs in .txt file with new IDs
else:
    log that there are "No entries"
```
