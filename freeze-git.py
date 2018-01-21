import discord
from discord.ext import commands
import random

import time
import sys
import logging
import datetime
from steem import Steem
from steem.post import Post
from steem.account import Account
from steem.amount import Amount
from steem.converter import Converter
from steembase.exceptions import PostDoesNotExist



global post, down_v, steem

steem = Steem(wif = "")

down_v =''

description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='?', description=description)

@bot.event
async def on_message(message):
    global post, msg_ch
    channel =  message.channel
    print(channel)
    if ('https://steemit.com' in message.content or 'https://busy.org' in message.content):
        enlaceE = message.embeds[0]['url']
        post= "@"+ str(enlaceE.split("@",1)[1])        
        cv(post)
        SteemInfo(post)
        await bot.send_message(channel, post_info+'```'+down_v+'```')
    else:
        print('Hi soy else')
    await bot.process_commands(message)
    
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')

# Get the post information
def SteemInfo(enlace):
    global post_info
    post = Post(enlace)

    if (post.cashout_time - datetime.datetime.now()).days < 0:
        i=[0,int((post.cashout_time - datetime.datetime.now()).seconds/3600)]
    else:
        i=[(post.cashout_time - datetime.datetime.now()).days,int((post.cashout_time - datetime.datetime.now()).seconds/3600)]    
    elap = [str(post.time_elapsed().days)+' dias y ', str(int(post.time_elapsed().seconds/60/24)) + ' horas' ]    
    post_info = "Autor: **{}** | Votos **{}** | $$$: **{:.2f}**, Vence en: **{}** Dias, y {} Horas \n\nPublicado el : **{}**, hace: {} {} ".format(post.author, post.net_votes,float(post.pending_payout_value),i[0],i[1], post.created,elap[0],elap[1] )
    return post_info
    
def cv(post:str):
    global down_v
    down_v =''
    post = Post(post)
    # *** Input steemit account to be used ***
    # *** The account's posting key need to exist in your Steempy wallet ***
    botname = 'bebeth'

    # Initializing steem-python objects
    steem = Steem(wif = "5JS81CUUDJpcW6tyXdED2fdZSaozypyDvM6TznFWw4zynL3yPLw")
    botf = Account(botname)

    # Setup logging
    logger = logging.getLogger('counterflag')
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler('vote.log', encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
    logger.addHandler(handler)

    # Used for conversion of steemit timestamp
    pattern = '%Y-%m-%dT%H:%M:%S'


    #logger.info('Starting countervote for: ' + post.url)
    total = 0
    # Loop through all votes
    for vote in post.active_votes:
        # Check if the bot already voted
        if(vote['voter'] == botname):
            print('Already voted on this post.')
            #logger.info('Already voted on this post.')
            total = 0
            break
        # Calculate the value of the flag and store it
        if(vote['percent'] < 0):
            user = Account(vote['voter'])
            flagValue = round(getrsharesvalue(vote['rshares']),4)
            print(vote['voter'] + ' downvoted the post with: $ ' + str(flagValue))
            down_v = down_v + vote['voter'] + ' downvoted the post with: $ ' + str(flagValue) +'\n'
            total += flagValue
            #print(down_v)

    # If there are flags, calculate the counter vote
    if(total < 0):
        print('Total downvoted value: $ ' + str(total) + '\n')
        down_v = down_v + '\n----------------------\nTotal downvoted value: $ ' + str(total) + '\n'
        
        #logger.info('Total downvoted value: $ ' + str(total))
        VP = getactiveVP(botf)
        SP = calculateSP(botf)
        VW = round(getvoteweight(SP, abs(total), VP),4)
        
        # Make sure the vote weight is max 100
        if(VW > 100):
            VW = 100
        print('Voting with ' + str(VW) + '% to try to counter the vote.')
        down_v = down_v + '\nVoting with ' + str(VW) + '% to try to counter the vote.'
        counterValue = round(getvotevalue(SP, VP, VW),4)
        print('Counter vote value comes to: $ ' + str(counterValue))
        down_v = down_v + '\nCounter vote value comes to: $ ' + str(counterValue)
        #logger.info('Voting with ' + str(VW) + '% with a value of: $ ' + str(counterValue))

        # Perform the vote
        try:
            print('vote!')            #post.upvote(weight=VW, voter=botname)
        except Exception:
            print('Failed to vote!')
            logger.error('Failed to vote!')
        else:
            print('Successfully voted')
            #logger.info('Successfully voted')

        return down_v
    else:
        print('Done.')
        down_v = "**No** downvotes or Flags found in Post"
        return down_v

    #await bot.say(down_v)
    
 
    
# Get the current upvote value based on rshares
def getrsharesvalue(rshares):
   
    conv = Converter()
    rew_bal = float(Amount(steem.steemd.get_reward_fund()['reward_balance']).amount)
    rec_claim = float(steem.steemd.get_reward_fund()['recent_claims'])
    steemvalue = rshares * rew_bal / rec_claim
    return conv.steem_to_sbd(steemvalue)

# Calculates the total SP
def calculateSP(account):
    allSP = float(account.get('vesting_shares').rstrip(' VESTS'))
    delSP = float(account.get('delegated_vesting_shares').rstrip(' VESTS'))
    recSP = float(account.get('received_vesting_shares').rstrip(' VESTS'))
    activeSP = account.converter.vests_to_sp(allSP - delSP + recSP)
    return activeSP

# Calculates the active voting power
def getactiveVP(account):
    # Used for conversion of steemit timestamp
    pattern = '%Y-%m-%dT%H:%M:%S'
    for event in account.get_account_history(-1,1000,filter_by='vote'):
        if(event['type'] == "vote"):
            if(event['voter'] == account.name):
                epochlastvote = int(time.mktime(time.strptime(event['timestamp'], pattern)))
                break
    timesincevote = int(time.time()) - epochlastvote
    VP = account.voting_power() + ((int(time.time())-epochlastvote) * (2000/86400)) / 100
    # Make sure the voting power is max 100
    if(VP > 100):
        VP = 100
    return VP

# Calculates the value of a vote
def getvotevalue(SP, VotingPower, VotingWeight):

    POWER = SP / (float(Amount(steem.steemd.get_dynamic_global_properties()['total_vesting_fund_steem']).amount) \
        / float(steem.steemd.get_dynamic_global_properties()['total_vesting_shares'].rstrip(' VESTS')))
    VOTING = ((100 * VotingPower * (100 * VotingWeight) / 10000) + 49) / 50
    REW = float(Amount(steem.steemd.get_reward_fund()['reward_balance']).amount) \
        / float(steem.steemd.get_reward_fund()['recent_claims'])
    PRICE = float(Amount(steem.steemd.get_current_median_history_price()['base']).amount) \
        / float(Amount(steem.steemd.get_current_median_history_price()['quote']).amount)
    VoteValue = (POWER * VOTING * 100) * REW * PRICE
    return VoteValue

# Calculates the voting weight
def getvoteweight(SP, VoteValue, VotingPower):

    POWER = SP / (float(Amount(steem.steemd.get_dynamic_global_properties()['total_vesting_fund_steem']).amount) \
        / float(steem.steemd.get_dynamic_global_properties()['total_vesting_shares'].rstrip(' VESTS')))
    REW = float(Amount(steem.steemd.get_reward_fund()['reward_balance']).amount) \
        / float(steem.steemd.get_reward_fund()['recent_claims'])
    PRICE = float(Amount(steem.steemd.get_current_median_history_price()['base']).amount) \
        / float(Amount(steem.steemd.get_current_median_history_price()['quote']).amount)
    VOTING = VoteValue / (POWER * 100 * REW * PRICE)
    VotingWeight = ((VOTING * 50 - 49) * 10000) / (100 * 100 * VotingPower)
    return VotingWeight


bot.run('token')