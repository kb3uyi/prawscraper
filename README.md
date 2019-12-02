# prawScraper

A simple reddit bot in python 3 that will download images from the posts you have saved.

## Authentication

The template authentication _template.json is provided, but you should set up your app reffering to the standard bot creation steps for a reddit account.
The praw project has excellent documentation for this: [praw.readthedocs.io](https://praw.readthedocs.io/en/v3.6.0/pages/writing_a_bot.html)
Choose a web app and include your client id/secret and all the other things in the template file in 'authenitcationm.json'. **Remember to .gitignore this file!**

## Dependencies 
These are in the pipfile but they include
* praw : Reddit API wrapper
  
    https://pypi.org/project/praw/
* tqdm : Pretty download graphs
  
    https://pypi.org/project/tqdm/
* requests : HTTP library
  
    https://pypi.org/project/requests/

## Command line Arguments
ArgumentParser is used to set up the following command line arguments.
```
usage: prawScraper.py [-h] [-s SUBREDDIT] [-l SAVED_LIMIT] [-v] -d
                      DOWNLOAD_DIR [-a AUTH_FILE] [-nsfw NSFW_FLAG] [-u]

Process saved reddit posts using 'authenitcation.json' account info.

optional arguments:
  -h, --help            show this help message and exit
  -s SUBREDDIT, --subreddit SUBREDDIT
                        subreddit to filter on, optional
  -l SAVED_LIMIT, --limit SAVED_LIMIT
                        limit number of saved posts
  -v, --verbose         increase output verbosity
  -d DOWNLOAD_DIR, --directory DOWNLOAD_DIR
                        directory to save images to
  -a AUTH_FILE, --authfile AUTH_FILE
                        json file for reddit authentication
  -nsfw NSFW_FLAG, --not_safe_for_work NSFW_FLAG
                        show nsfw posts: none, include, exclusive
  -u, --unsave          unsave the posts that get downloaded
  ```
## Notes:

* The limit arguement is used like ``reddit.user.me().saved(limit=saved_limit)``
    * It seems like the unlimited call to .saved() still only responds with a small number of posts.
    * This could be a limitation of the reddit API, I dont know. The web UI has limits and even RES only loads posts a few at a time.
* Repeatedly calling this script with unsaved and a large limit is the best way to download all images.
    * with a small limit like 100, you could reach a state where you have 100 self posts in a row without an image.
    * Unsaving and running again would still result in no images if you did that.
    * Perhaps in the future I could implement a real no limit mode by automatically unsaving and re-running many times until there really are no images left.