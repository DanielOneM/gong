import telnetlib


def change_jasmin(host='localhost',
                  port=8990,
                  user='jcliadmin',
                  password='jclipwd',
                  gong_user='test',
                  gong_pass='default',
                  gong_host='172.25.0.4',
                  gong_port='2775',
                  debuglevel=50):

    tn = telnetlib.Telnet(host, port)
    tn.set_debuglevel(debuglevel)

    tn.read_until("Username:", 5)
    tn.write(user + "\n")
    if password:
        tn.read_until("Password:", 5)
        tn.write(password + "\n")

    tn.read_until('jcli : ')
    tn.write("smppccm -l\n")
    f = tn.read_until('jcli : ')

    active_gong = False
    for item in f.split('\r\r\r\n')[2:-1]:
        if 'gong' in item:
            active_gong = True
            break

    if not active_gong:
        tn.write('smppccm -a\n')
        commands = 'cid gong;username {};password {};host {};port {};ok'.format(gong_user, gong_pass, gong_host, gong_port)
        for entry in commands.split(';'):
            tn.read_until('> ')
            tn.write(entry + '\n')

        tn.read_until('jcli : ')
        tn.write("smppccm -1 gong\n")

    tn.write('quit\n')
    tn.close()

    return True

if __name__ == '__main__':
    change_jasmin()
