from cpucoolerchart import config


def test_Config_from_envvars():
    config.os.environ = {
        'INT': '1',
        'FLOAT': '2.5',
        'TRUE': 'True',
        'FALSE': 'False',
        'ARRAY': '[a, b, c]',
        'STRING': 'foobar',
        'LOGGING.a.b.c': '1',
        'LOGGING."a.b".c': 'd',
        'LOGGING.a."b.c"': 'd',
    }
    config.Config.from_envvars()
    assert config.Config.INT == 1
    assert config.Config.FLOAT == 2.5
    assert config.Config.TRUE is True
    assert config.Config.FALSE is False
    assert config.Config.ARRAY == ['a', 'b', 'c']
    assert config.Config.STRING == 'foobar'
    assert config.Config.LOGGING['a']['b']['c'] == 1
    assert config.Config.LOGGING['a.b']['c'] == 'd'
    assert config.Config.LOGGING['a']['b.c'] == 'd'


def test_Config_setup_gmail_smtp():
    handler = config.Config.LOGGING['handlers']['mail_admins']
    config.Config.setup_gmail_smtp()
    assert handler['mailhost'] == 'localhost'
    config.Config.MAIL_TOADDRS = ['foo@bar.org']
    config.Config.GMAIL_USERNAME = 'user@gmail.com'
    config.Config.GMAIL_PASSWORD = 'letmein'
    config.Config.setup_gmail_smtp()
    assert handler['toaddrs'] == ['foo@bar.org']
    assert handler['mailhost'] == ('smtp.gmail.com', 587)
    assert handler['credentials'] == ('user@gmail.com', 'letmein')
    assert handler['secure'] == ()
    assert ('mail_admins' in
            config.Config.LOGGING['loggers']['cpucoolerchart']['handlers'])
