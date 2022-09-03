import aiohttp
import asyncio
import re
import argparse
import sys

user = 'admin'
password  = 'your_password_here'
ip = 'your_switch_ip_here'

async def get_state_once(user,password,ip):

    async with aiohttp.ClientSession() as session:
        async with session.get('http://' + ip + '/adm/relay_control.asp', auth=aiohttp.BasicAuth(user, password)) as response:
            status = response.status
            result = await response.text()
            
    if status != 200:
        return None
    
    matches = re.search('s = \"([01])\"',result)

    rawstate = matches.group(1) if matches is not None else None

    state = True if (rawstate == '1') else False if (rawstate == '0') else None

    return state

async def get_state(user,password,ip):
    state = None
    i = 0
    
    # the "smart plug" will always return 401 unauthorized to the first request it receives after 5
    # or more minutes have elapsed, therefore we try to get the state up to 2 times before continuing
    while state is None and i < 2:
        state = await get_state_once(user,password,ip)
        i += 1
 
    # Handle None after retry, as it indicates a legitimate connection error.
    if state is None:
        print('Connection or authentication error: Check device\'s network connection and password')
        sys.exit(1)
 
    return state

async def get_key(user,password,ip):

    async with aiohttp.ClientSession() as session:
        async with session.get('http://' + ip + '/goform/UpdateKey', auth=aiohttp.BasicAuth(user, password)) as response:
            key = await response.text()

    return key
    
async def toggle(user,password,ip,state = None):

    if state is None:
        state = await get_state(user,password,ip)

    old_state = state

    while old_state == state:
        params = {'form_key' : await get_key(user,password,ip)}
    
        async with aiohttp.ClientSession() as session:
            async with session.get('http://' + ip + '/goform/RelayOnOff', params=params, auth=aiohttp.BasicAuth(user, password)) as response:
                pass
        
        state = await get_state(user,password,ip)
    
    return state

async def turn_on(user,password,ip):

    state = await get_state(user,password,ip)
    
    if state is False:
        state = await toggle(user,password,ip,state)
        
    return state
    
async def turn_off(user,password,ip):

    state = await get_state(user,password,ip)
    
    if state is True:
        state = await toggle(user,password,ip,state)
        
    return state

options = {'on': turn_on,
           'off': turn_off,
           'toggle': toggle,
           'state': get_state}


async def main():

    parser = parser = argparse.ArgumentParser(description='Operates TrendNet THA-101 Wi-Fi smart switch')
    parser.add_argument('command', default='toggle', choices=['on','off','toggle','state'], nargs='?')
    args = parser.parse_args()

    result = await options[args.command](user,password,ip)
    
    print(result)

asyncio.run(main())

