c = ASTFClient("127.0.0.1")

c.connect()
c.reset()

if not profile_path:
    profile_path = os.path.join(astf_path.ASTF_PROFILES_PATH, 'http_simple.py')

c.load_profile(profile_path)
c.clear_stats()
c.start(mult="100%", duration=10)

c.wait_on_traffic()
stats = c.get_stats()

# use this for debug info on all the stats
print(stats)

if c.get_warnings():
    print('\n\n*** test had warnings ****\n\n')
    for w in c.get_warnings():
         print(w)
