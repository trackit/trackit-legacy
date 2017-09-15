# [PUBLIC] How to start

## Steps to run TrackitIo
  - `# git clone [git repository]`
  - `# cd [git repository]`
  - `# docker-compose up`
  - Go on localhost and enjoy!

## Default credentials
```
email: demo@demo.io
password: mypassword
```

# [INTERN] How to deploy

Once you have made your feature, merge it to the dev branch. 
The dev branch should have all the commits before they are made on the master and the production branch. 
The dev branch must be updated as often as possible.

Just merge to the master branch to deploy on staging.trackit.io
Once your work is reviewed, you can deploy on the production by merging the master branch to the production branch.
Only the master branch should be merged in the production branch.
