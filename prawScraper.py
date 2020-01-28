# prawScraper.py

import praw
import json
import sys
from argparse import ArgumentParser
from tqdm import tqdm
import requests
import math
from os import path

class prawScraper:

    # Class Variables
    allowedFiletypes = (".jpg",".png",".gif")

    def main(argv):
        """Main function for fetching saved reddit posts

        Arguments: None
        Command Line Arguments:
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
        """
        parser = ArgumentParser(description='Process saved reddit posts using \'authenitcation.json\' account info.')
        parser.add_argument("-s", "--subreddit", dest="subreddit",
                            help="subreddit to filter on, optional", metavar="SUBREDDIT")
        parser.add_argument("-l", "--limit", dest="limit", type=int,
                            help="limit number of saved posts", metavar="SAVED_LIMIT")
        parser.add_argument("-v", "--verbose", help="increase output verbosity",
                            action="store_true")
        parser.add_argument("-d", "--directory", dest="directory", required=True,
                            help="directory to save images to", metavar="DOWNLOAD_DIR")
        parser.add_argument("-a", "--authfile", dest="authfile",
                            help="json file for reddit authentication", metavar="AUTH_FILE")
        parser.add_argument("-nsfw", "--not_safe_for_work", dest="nsfw",
                            help="show nsfw posts: none, include, exclusive", metavar="NSFW_FLAG")
        parser.add_argument("-u", "--unsave", help="unsave the posts that get downloaded", action="store_true")

        # TODO: add an argument to prompt for credentials. leave authfile for client and secret.
        # TODO: add an argument for additional file types.

        args = parser.parse_args()

        if args.authfile is None:
            args.authfile =  './authentication.json'
        if args.nsfw is None:
            args.nsfw =  'none'

        prawScraper.scrape(args.subreddit, args.limit, args.verbose, args.directory, args.authfile, args.nsfw, args.unsave)

    def scrape(subreddit, limit, verbose, downloadDir, authFile, nsfw, unsave):
        """Function to loop over the saved reddit posts.

        Arguments:
            subreddit {string} -- subreddit to check (null for all subreddits)
            limit {int} -- limit of posts to fetch in a single call
            verbose {boolean} -- set output verbosity
            downloadDir {string} -- destination of saved files
            authFile {string} -- path to the authentication file
            nsfw {string} -- set nsfw inclusion: none, include, exclusive
            unsave {boolean} -- should processed posts be unsaved
        """
        with open(authFile) as f:
            auth_data = json.load(f)

        # ? things not in the JSON file are null right?
        # TODO add the check that username and password should be prompted.

        reddit = praw.Reddit(client_id      = auth_data['client_id'],
                             client_secret  = auth_data['client_secret'],
                             password       = auth_data['password'],
                             user_agent     = auth_data['user_agent'],
                             username       = auth_data['username']
                             )

        if verbose:
            print(reddit.user.me())
            print("Download Directory: " + downloadDir)

        # set read only mode
        # reddit.read_only = True

        subreddit_name  = subreddit
        saved_limit     = limit
        subreddit_selected = True

        if subreddit_name is None or subreddit_name == "none":
            subreddit_selected = False
        else:
            subreddit_selected = True
            selected_sub = reddit.subreddit(subreddit_name)
            if verbose:
                print("Selected subredit name: " + selected_sub.name)
                print("Selected subredit id: " + selected_sub.id)

        if saved_limit is None:
            saved = reddit.user.me().saved()
        else:
            saved = reddit.user.me().saved(limit=saved_limit)

        for post in saved:
            try:
                if isinstance(post, praw.models.Submission):
                    if subreddit_selected == True:
                        if post.subreddit_id == selected_sub.name:
                            prawScraper.process_post(post, verbose, downloadDir, nsfw, unsave)
                    else:
                        prawScraper.process_post(post, verbose, downloadDir, nsfw, unsave)
            except AttributeError as err:
                print(err)

    def process_post(post, verbose, downloadDir, nsfw, unsave):
        """Function to process individual posts from the set of fetched posts

        Arguments:
            post {string} -- fetched post URL
            verbose {boolean} -- set output verbosity
            downloadDir {string} -- destination of saved files
            authFile {string} -- path to the authentication file
            nsfw {string} -- set nsfw inclusion: none, include, exclusive
            unsave {boolean} -- should processed posts be unsaved
        Returns:
            None
        """
        if nsfw == "none" and post.over_18:
            return # This post cannot be included in a worksafe run
        if nsfw == "exclusive" and not post.over_18:
            return # This post cannot be indluded in a non-worsafe run
        # The 'included' case is a free for all

        if post.is_self:    return

        # submission link is at post.url, separate the extension
        extension = path.splitext(post.url)[1].split("?")[0]
        filename =  path.basename(path.splitext(post.url)[0])

        if any(matchExt in extension for matchExt in prawScraper.allowedFiletypes):
            # s in extension for s in prawScraper.allowedFiletypes
            # filetype allowed, download
            if verbose:
                # print("filename: " + filename)
                # print("extension: " + extension)
                print(post.url + " : " + filename + extension)

            # Streaming, so we can iterate over the response.
            r = requests.get(post.url, stream=True)
            # To save to a relative path.
            #r = requests.get(url)
            with open(downloadDir + filename + extension, 'wb') as f:
                f.write(r.content)

            # Total size in bytes.
            total_size = int(r.headers.get('content-length', 0));
            block_size = 1024
            wrote = 0
            with open('output.bin', 'wb') as f:
                for data in tqdm(r.iter_content(block_size), total=math.ceil(total_size//block_size) , unit='KB', unit_scale=True):
                    wrote = wrote  + len(data)
                    f.write(data)
            if total_size != 0 and wrote != total_size:
                print("ERROR, something went wrong")

            if unsave:
                if verbose:

                    print(post.url + " (" + filename + extension + ") was unsaved.")
                post.unsave()

if __name__ == "__main__":
   """call class main
   """
   prawScraper.main(sys.argv[1:])