#coding:utf-8
#
# @author yufb116689@hanslaser.com
# @date 2016-05-15
#
import sys
from mobiapp_core import *

class MobiAppFactory(object):
    def __init__(self, host, port, log_filename = None):
        self.host = host
        self.port = port
        self.default_username = None

        self.all_mobiapp_dict = {}
        self.stopped_mobiapp_dict = {}
        self.running_mobiapp_dict = {}
        self.scheduling_mobiapp_queue = []
        self.scheduling_mobiapp_dict = {}

        self.log_filename = None
        self.init_logfile(log_filename)

    def __del__(self):
        self.close_logfile()

    def output(self, username, msg):
        print >>self.log_file, datetime.datetime.now(), username, msg
        #self.log_file.flush()

    def show_info(self):
        print "host: %s" % self.host
        print "port: %d" % self.port
        print "default_username: %s" % self.default_username
        print "log_filename: %s" % self.log_filename

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

    def mobiapp_exists(self, username):
        return self.all_mobiapp_dict.has_key(username)

    def build_mobiapp(self, username, password):
        if self.mobiapp_exists(username):
            print "MobiApp %s exists" % username
            return None
        else:
            mobiapp = MobiApp(self, username, password)
            self.all_mobiapp_dict[username] = mobiapp
            self.stopped_mobiapp_dict[username] = mobiapp
            print "Create MobiApp %s successful" % username
            return mobiapp

    def build_mobiapp_batch(self, username_prefix, begin_index, end_index):
        for idx in xrange(begin_index, end_index):
            username = self._gen_username(username_prefix, idx)
            password = username
            self.build_mobiapp(username, password)
        print "Created %d MobiApps" % len(self.stopped_mobiapp_dict)

    def get_stopped_mobiapp(self, username):
        if self.stopped_mobiapp_dict.has_key(username):
            return self.stopped_mobiapp_dict[username]
        else:
            return None

    def get_running_mobiapp(self, username):
        if username in self.running_mobiapp_dict:
            return self.running_mobiapp_dict[username]
        else:
            return None

    def list_mobiapps(self, which, pnum = 10):
        if which == 'stopped':
            print 'stopped[%d]:       %s' % (len(self.stopped_mobiapp_dict), self.stopped_mobiapp_dict.keys()[:pnum])
        elif which == 'running':
            print 'running[%d]:       %s' % (len(self.running_mobiapp_dict), self.running_mobiapp_dict.keys()[:pnum])
        elif which == 'scheduling':
            print 'scheduling[%d]:    %s' % (len(self.scheduling_mobiapp_dict), self.scheduling_mobiapp_dict.keys()[:pnum])
        else:
            print 'stopped[%d]:       %s' % (len(self.stopped_mobiapp_dict), self.stopped_mobiapp_dict.keys()[:pnum])
            print 'running[%d]:       %s' % (len(self.running_mobiapp_dict), self.running_mobiapp_dict.keys()[:pnum])
            print 'scheduling[%d]:    %s' % (len(self.scheduling_mobiapp_dict), self.scheduling_mobiapp_dict.keys()[:pnum])
            print 'default(selected): %s' % self.default_username

    def show_mobiapp_info(self, username):
        if self.mobiapp_exists(username):
            mobiapp = self.all_mobiapp_dict[username]
            mobiapp.show_info()
        else:
            print "Unknown MobiApp: ", username

    def has_default_mobiapp(self):
        return self.default_username is not None

    def get_default_mobiapp(self):
        return self.all_mobiapp_dict[self.default_username] if self.default_username else None

    def get_default_username(self):
        return self.default_username

    def set_default_mobiapp(self, username):
        if self.mobiapp_exists(username):
            if self.default_username:
                if self.default_username != username:
                    self.clear_default_mobiapp()
                    self.default_username = username
                    self.all_mobiapp_dict[username].set_interactive_mode(True)
                    print "Successful"
                else:
                    print "%s already is default MobiApp" % username
            else:
                self.default_username = username
                self.all_mobiapp_dict[username].set_interactive_mode(True)
            return True
        else:
            print "MobiApp %s not exists" % username
            return False

    def clear_default_mobiapp(self):
        if self.default_username:
            self.all_mobiapp_dict[self.default_username].set_interactive_mode(False)
            self.default_username = None

    def run_mobiapp(self, username, automation=False):
        if self.stopped_mobiapp_dict.has_key(username):
            mobiapp = self.stopped_mobiapp_dict[username]
            mobiapp.set_automation(automation)
            del self.stopped_mobiapp_dict[username]
            self.scheduling_mobiapp_queue.append(mobiapp)
            self.scheduling_mobiapp_dict[username] = mobiapp
            factory = MobiAppProtocolFactory(self)
            reactor.connectTCP(self.host, self.port, factory)
            print 'MobiApp %s starting, connect to %s:%d.' % (username, self.host, self.port)
        elif self.running_mobiapp_dict.has_key(username):
            print "MobiApp %s already running" % username
        else:
            print "MobiApp %s not exists" % username

    def stop_mobiapp(self, username):
        if self.running_mobiapp_dict.has_key(username):
            mobiapp = self.running_mobiapp_dict[username]
            mobiapp.stop()
            print "MobiApp %s stopped" % username
        elif self.stopped_mobiapp_dict.has_key(username):
            print "MobiApp %s not running" % username
        else:
            print "MobiApp %s not exists" % username

    def run_all_mobiapps(self, automation=False):
        num = len(self.stopped_mobiapp_dict)
        for username in self.stopped_mobiapp_dict.keys():
            self.run_mobiapp(username, automation)
        print "Run %d MobiApps" % num

    def stop_all_mobiapps(self):
        num = len(self.running_mobiapp_dict)
        for mobiapp in self.running_mobiapp_dict.values():
            mobiapp.stop()
        print "Stopped %d MobiApps" % num

    def takeout_scheduling_mobiapp(self):
        mobiapp = None
        if self.scheduling_mobiapp_queue:
            mobiapp = self.scheduling_mobiapp_queue.pop(0)
            del self.scheduling_mobiapp_dict[mobiapp.get_username()]
            self.running_mobiapp_dict[mobiapp.get_username()] = mobiapp
        return mobiapp

    def recycle_stopped_mobiapp(self, mobiapp):
        del self.running_mobiapp_dict[mobiapp.get_username()]
        self.stopped_mobiapp_dict[mobiapp.get_username()] = mobiapp

    def _gen_username(self, prefix, idx):
        return prefix + str(idx)
