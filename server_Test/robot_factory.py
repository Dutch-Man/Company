# -*- coding: utf-8 -*-
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#
from robot_core import *

class RobotFactory(object):
    def __init__(self, host, port, log_filename = None):
        self.host = host
        self.port = port
        self.default_devsn = None

        self.stopped_robot_dict = {}
        self.running_robot_dict = {}
        self.scheduling_robot_queue = []
        self.scheduling_robot_dict = {}

        self.log_filename = None
        self.init_logfile(log_filename)

    def __del__(self):
        self.close_logfile()

    def show_info(self):
        print "host: %s" % self.host
        print "port: %d" % self.port
        print "default_username: %s" % self.default_devsn
        print "log_filename: %s" % self.log_filename

    def log(self, devsn, msg):
        print >>self.log_file, datetime.datetime.now(), devsn, msg
        #self.log_file.flush()

    def init_logfile(self, filename):
        self.log_filename = filename
        if self.log_filename:
            self.log_file = open(self.log_filename, 'a+')
        else:
            self.log_file = sys.stdout

    def close_logfile(self):
        if self.log_filename:
            self.log_file.close()
            import os
            if os.stat(self.log_filename).st_size == 0:
                os.remove(self.log_filename)

    def change_logfile(self, filename):
        self.close_logfile()
        self.init_logfile(filename)
        print "log file changed to %s" % filename

    def flush_log(self):
        self.log_file.flush()

    def robot_exists(self, devsn):
        return self.stopped_robot_dict.has_key(devsn) or \
                self.running_robot_dict.has_key(devsn) or \
                self.scheduling_robot_dict.has_key(devsn)

    def build_robot(self, devsn, registered=True):
        if self.robot_exists(devsn):
            print "Robot %s exists" % devsn
            return None
        else:
            robot = Robot(self, devsn, registered)
            self.stopped_robot_dict[devsn] = robot
            print "Create robot %s successful" % devsn
            return robot

    def build_robot_batch(self, devsn_prefix, begin_index, end_index, registered=True):
        for idx in xrange(begin_index, end_index):
            devsn = self._gen_devsn(devsn_prefix, idx)
            self.build_robot(devsn, registered)
        print "Created %d robots" % len(self.stopped_robot_dict)

    def get_stopped_robot(self, devsn):
        if self.stopped_robot_dict.has_key(devsn):
            return self.stopped_robot_dict[devsn]
        else:
            return None

    def get_running_robot(self, devsn):
        if devsn in self.running_robot_dict:
            return self.running_robot_dict[devsn]
        else:
            return None

    def list_robots(self, which, pnum = 10):
        if which == 'stopped':
            print 'stopped[%d]:    %s' % (len(self.stopped_robot_dict), self.stopped_robot_dict.keys()[:pnum])
        elif which == 'running':
            print 'running[%d]:    %s' % (len(self.running_robot_dict), self.running_robot_dict.keys()[:pnum])
        elif which == 'scheduling':
            print 'scheduling[%d]: %s' % (len(self.scheduling_robot_dict), self.scheduling_robot_dict.keys()[:pnum])
        else:
            print 'stopped[%d]:    %s' % (len(self.stopped_robot_dict), self.stopped_robot_dict.keys()[:pnum])
            print 'running[%d]:    %s' % (len(self.running_robot_dict), self.running_robot_dict.keys()[:pnum])
            print 'scheduling[%d]: %s' % (len(self.scheduling_robot_dict), self.scheduling_robot_dict.keys()[:pnum])
            print 'default:    ', self.default_devsn

    def show_robot_info(self, devsn):
        robot = None
        if self.running_robot_dict.has_key(devsn):
            robot = self.running_robot_dict[devsn]
        elif self.stopped_robot_dict.has_key(devsn):
            robot = self.stopped_robot_dict[devsn]
        else:
            print "Unknown robot: ", devsn
            return
        robot.show_info()

    def has_default_robot(self):
        return self.default_devsn is not None

    def get_default_robot(self):
        return self.default_devsn

    def set_default_robot(self, devsn):
        if self.robot_exists(devsn):
            self.default_devsn = devsn
            print "Successful"
        else:
            print "Robot %s not exists" % devsn

    def run_robot(self, devsn):
        if self.stopped_robot_dict.has_key(devsn):
            robot = self.stopped_robot_dict[devsn]
            del self.stopped_robot_dict[devsn]
            self.scheduling_robot_queue.append(robot)
            self.scheduling_robot_dict[devsn] = robot
            factory = RobotProtocolFactory(self)
            reactor.connectTCP(self.host, self.port, factory)
            print 'Robot %s starting, connect to %s:%d.' % (devsn, self.host, self.port)
        elif self.running_robot_dict.has_key(devsn):
            print "Robot %s already running" % devsn
        else:
            print "Robot %s not exists" % devsn

    def stop_robot(self, devsn):
        if self.running_robot_dict.has_key(devsn):
            robot = self.running_robot_dict[devsn]
            robot.stop()
            print "Robot %s stopped" % devsn
        elif self.stopped_robot_dict.has_key(devsn):
            print "Robot %s not running" % devsn
        else:
            print "Robot %s not exists" % devsn

    def run_all_robots(self):
        num = len(self.stopped_robot_dict)
        for devsn in self.stopped_robot_dict.keys():
            self.run_robot(devsn)
        print "Run %d robots" % num

    def stop_all_robots(self):
        num = len(self.running_robot_dict)
        for robot in self.running_robot_dict.values():
            robot.stop()
        print "Stop %d robots" % num

    def takeout_scheduling_robot(self):
        robot = None
        if self.scheduling_robot_queue:
            robot = self.scheduling_robot_queue.pop(0)
            del self.scheduling_robot_dict[robot.get_devsn()]
            self.running_robot_dict[robot.get_devsn()] = robot
        return robot

    def recycle_stopped_robot(self, robot):
        del self.running_robot_dict[robot.get_devsn()]
        self.stopped_robot_dict[robot.get_devsn()] = robot

    def _gen_devsn(self, prefix, idx):
        return prefix + str(idx)
