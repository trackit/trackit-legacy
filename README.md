# TrackIt deployment

## Setup ssh forwarder

Our scripts don't support git interactive mode, so you need to make sure you use git-ssh

```
ludo@idefix:~ % tail -4 .ssh/config
Host jenkins
hostname jenkins.msolution.io
ForwardAgent yes
user ludo
ludo@idefix:~ %
```

## Connect to jenkins host

```
ludo@idefix:~ % ssh jenkins
```

## git clone the infra repo

```
ludo@jenkins ~ $ git clone git@bitbucket.org:msolutionio/infrastructure.trackit.io.git
Cloning into 'infrastructure.trackit.io'...
remote: Counting objects: 352, done.
remote: Compressing objects: 100% (326/326), done.
remote: Total 352 (delta 169), reused 0 (delta 0)
Receiving objects: 100% (352/352), 89.34 KiB | 137.00 KiB/s, done.
Resolving deltas: 100% (169/169), done.
Checking connectivity... done.
ludo@jenkins ~ $
```

## export your AWS credentials (admin permissions)

```
ludo@jenkins ~ $ cd infrastructure.trackit.io/
ludo@jenkins ~/infrastructure.trackit.io $ export AWS_ACCESS_KEY=XXXXXXXXXXXXXXXX
ludo@jenkins ~/infrastructure.trackit.io $ export AWS_SECRET_ACCESS_KEY=YYYYYYYYYYYY
ludo@jenkins ~/infrastructure.trackit.io $ export AWS_DEFAULT_REGION=us-west-2
```

## make sure aws cli tool is ready

```
ludo@jenkins ~/infrastructure.trackit.io $ aws configure
AWS Access Key ID [****************O7KA]:
AWS Secret Access Key [****************qKOF]:
Default region name [us-west-2]:
Default output format [None]:
ludo@jenkins ~/infrastructure.trackit.io $
```

## make sure you have terraform packages

``` 
ludo@jenkins:~/infrastructure.trackit.io/terraform⟫ terraform get
Get: file:///home/ludo/infrastructure.trackit.io/terraform/vpc
Get: file:///home/ludo/infrastructure.trackit.io/terraform/db
Get: file:///home/ludo/infrastructure.trackit.io/terraform/elb
Get: git::ssh://git@bitbucket.org/msolutionio/infrastructure.trackit.io.git
Get: file:///home/ludo/infrastructure.trackit.io/terraform/app
Get: file:///home/ludo/infrastructure.trackit.io/terraform/dns
ludo@jenkins:~/infrastructure.trackit.io/terraform⟫
```

## ./auto-deploy.sh

```
ludo@jenkins:~/infrastructure.trackit.io⟫ ./auto-deploy.sh

Apply complete! Resources: 0 added, 0 changed, 2 destroyed.

Outputs:

api_endpoint = api.trackit.io
docs_endpoint = docs.trackit.io
elb_endpoint = trackitprodelb-1617672053.us-west-2.elb.amazonaws.com
elb_id = trackitprodelb
elb_name = trackitprodelb
es_endpoint = search-trackit-hrsvg2i4b6skger3ilplihs7cy.us-west-2.es.amazonaws.com
mariadb_endpoint = tf-6wtjoh7isrb2zcctbfkyb2p4wy.cmq6lom8tstw.us-west-2.rds.amazonaws.com:3306
redis_endpoint = trackit-cluster.sic6dm.0001.usw2.cache.amazonaws.com
ui_endpoint = trackit.io
vpc_id = vpc-6760fb03
www_endpoint = www.trackit.io
Is the infrastructure ready for destructive changes? Are all instances in service? (y/N): [master 22211b6] Deploy ami-65ba6405.
 Committer: Ludovic Francois <ludo@jenkins.msolution.io>
Your name and email address were configured automatically based
on your username and hostname. Please check that they are accurate.
You can suppress this message by setting them explicitly:

    git config --global user.name "Your Name"
    git config --global user.email you@example.com

After doing this, you may fix the identity used for this commit with:

    git commit --amend --reset-author

 2 files changed, 28 insertions(+), 28 deletions(-)
ludo@jenkins:~/infrastructure.trackit.io⟫
```

## Don't forget to push the commit

```
ludo@jenkins:~/infrastructure.trackit.io⟫ git config --global user.name "Ludovic Francois"
ludo@jenkins:~/infrastructure.trackit.io⟫ git config --global user.email ludo@msolution.io
ludo@jenkins:~/infrastructure.trackit.io⟫ git commit --amend --reset-author
[master 2ea92be] Deploy ami-65ba6405.
 2 files changed, 28 insertions(+), 28 deletions(-)
ludo@jenkins:~/infrastructure.trackit.io⟫ git push
warning: push.default is unset; its implicit value is changing in
Git 2.0 from 'matching' to 'simple'. To squelch this message
and maintain the current behavior after the default changes, use:

  git config --global push.default matching

To squelch this message and adopt the new behavior now, use:

  git config --global push.default simple

When push.default is set to 'matching', git will push local branches
to the remote branches that already exist with the same name.

In Git 2.0, Git will default to the more conservative 'simple'
behavior, which only pushes the current branch to the corresponding
remote branch that 'git pull' uses to update the current branch.

See 'git help config' and search for 'push.default' for further information.
(the 'simple' mode was introduced in Git 1.7.11. Use the similar mode
'current' instead of 'simple' if you sometimes use older versions of Git)

Counting objects: 16, done.
Delta compression using up to 8 threads.
Compressing objects: 100% (9/9), done.
Writing objects: 100% (9/9), 1.03 KiB | 0 bytes/s, done.
Total 9 (delta 6), reused 0 (delta 0)
To git@bitbucket.org:msolutionio/infrastructure.trackit.io.git
   7132c12..2ea92be  master -> master
ludo@jenkins:~/infrastructure.trackit.io⟫
```