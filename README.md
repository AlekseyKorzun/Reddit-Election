Reddit Election
===============

This is a simple Python based election system that gives you ability to upvote/downvote Reddit users with a set number of voters.

I wrote this code as I was playing around with Python. Use it at your own risk, I shall accept no liability on my part.

Usage
===============

Simply run the election.py with --target and --voters arguments. For example: 

```
python election.py --candidate username --voters voter1:password,voter2:password
```

By default the script will 'elect' candidate by upvoting his/her comments, you can switch to downvoting by passing an --elect 0 argument
