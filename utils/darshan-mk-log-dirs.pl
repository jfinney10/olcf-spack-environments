#!/usr/bin/perl -w
#
# Copyright (C) 2015 University of Chicago.
# See COPYRIGHT notice in top-level directory.
#

use File::Basename;

# creates a hierarchy of subdirectories for darshan to place log files in
# LOGDIR/<year>/<month>/<day>/

$number_args = $#ARGV + 1;  
if ($number_args != 1) {  
  print "ERROR: Please enter this system's cannonical name.\n";  
  exit;  
}  

$systemName=$ARGV[0];

# use log dir specified at configure time
$LOGDIR = "/gpfs/alpine/darshan/$systemName";

my $year = (localtime)[5] + 1900;
my $month;
my $day;
my $i;
my $j;
my $k;

umask(0);

# go through the end of next year
for ($i=$year; $i<($year+2); $i++)
{
    mkdir("$LOGDIR/$i", 0755) or die("Error: could not mkdir $LOGDIR/$i.\n");
    for ($j=1; $j<13; $j++)
    {
        mkdir("$LOGDIR/$i/$j", 0755) or die("Error: could not mkdir $LOGDIR/$i/$j.\n");
        for ($k=1; $k<32; $k++)
        {
            mkdir("$LOGDIR/$i/$j/$k", 01777) or die("Error: could not mkdir $LOGDIR/$i/$j/$k.\n");

        }
    }
}


