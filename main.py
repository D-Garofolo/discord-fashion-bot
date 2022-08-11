import discord
import requests
from aws import getDesigner, addDesigner, getRunway, updateRunway
from bs4 import BeautifulSoup
import os
import math
import json
import time

client = discord.Client()
#Public array used for runway fetching and indices matching
emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"] 
skip_button = "⏭️"
vote_emojis = ["👍", "👎"]

@client.event
async def on_message(message):
  #Runway command, finds all collections on Vogue from a given designer, then allow user to specify which runway they want via reactions
  if message.content.startswith('$runway'):
    args = message.content.lower().split()[1:]
    designer_name = ' '.join(args)

    #Call to backend and see if designer already exists in backend, if not, scrape webpage to get information via BeautifulSoup
    table = getDesigner(designer_name)
    if (not 'Item' in table):
      url = "https://www.vogue.com/fashion-shows/designer/" + '-'.join(args)
      response = requests.get(url)
      soup = BeautifulSoup(response.content, "html.parser")
      
      #If user input leads to an invalid page, return error message.
      invalidPage = (soup.find("title").text == "Page Not Found | Vogue")
      if (invalidPage):
        await message.channel.send("No runways found. Correct usage is *$runway <designer name>*.")
        return
        
      #Use beautifulSoup to parse through designer's webpage and find the thumbnails for all collections posted on Vogue under that designer.  
      else:
        results = soup.findAll("script", type="text/javascript", text=True)
        parse = results[1].string
        start = parse.index("designerCollections")
        end = parse.index("promoImage")

        #Collection information is stored within json, create clean json and parse it to get all the collection titles and urls
        parse = "{" + parse[start - 1:end - 2] + "}"
        results = json.loads(parse)
        results = results["designerCollections"]
        res = []
        
        #Gather the title and urls of all collections on the page 
        for result in results:
          title = result['hed']
          show_url = "https://www.vogue.com" + result['url']
          elem = {
            "Collection Title" : title,
            "URL" : show_url,
            "Score" : 0,
            "TotalVotes" : 0
          }
          res.append(elem)

        #Add it to backend and then re-retrieve it in the format stored in the backend for a singular method of displaying data regardless of initial condition
        addDesigner(designer_name, res)
        table = getDesigner(designer_name)
    
    items = table['Item']['Collections']
    res = ""
    
    #Gather the title and urls of all collections on the page 
    for i in range(min(10, len(items))):
      run_title = items[i]["Collection Title"]
      res += emojis[i] + " " + run_title + "\n"

    #Create and send an embed with all the information gathered
    res += "⏭️ for more collections"
    embed = discord.Embed(title=designer_name, description=res)

    #Footer is used to store relative scope of data visible to user, will be used to split data into pages and avoid walls of text in display
    footer_txt = "Page 1 / " + str(math.ceil(len(items) / 10))
    embed.set_footer(text=footer_txt)
    temp = await message.channel.send(embed=embed)

    #Emoji reactions can be used for a user to specify which collection they want to display after message is sent
    for emoji in emojis:
      await temp.add_reaction(emoji)
    await temp.add_reaction(skip_button)

  #Topcollections command, gathers information on runway and displays the top 5 most highly rated collections based on previous user input
  if message.content.startswith('$topcollections'):
    #Fetch information from backend, if designer isn't cached or exists, return error message.
    args = message.content.lower().split()[1:]
    designer_name = ' '.join(args)
    table = getDesigner(designer_name)
    if (not 'Item' in table):
      await message.channel.send("No information on this designer found. Correct usage is *$topcollections <designer name>*.")
      return

    #Iterate through table, if there are no votes, don't add them to the array to be sorted (prevents divide by zero error later down the line)
    ans = []
    for collection in table['Item']['Collections']:
      if (collection['TotalVotes'] > 0):
        ans.append(collection)

    #Comparator necessary for sorting since sorting condition depends on 2 variables
    def comparator(x):
      return -(x['Score']/x['TotalVotes'])

    ans = sorted(ans, key=comparator)

    #Use sorted array to display a message with the top 5 rated collections
    ranking_message_txt = ""
    for i in range(min(5, len(ans))):
      ranking_message_txt += ans[i]['Collection Title'] + " : " + str(round(ans[i]['Score'] / ans[i]['TotalVotes'] * 100)) + "% approval rating (" + str(ans[i]['TotalVotes']) + " ratings overall)\n"

    ranking_message_title = "Top 5 " + designer_name + " collections"
    
    embed = discord.Embed(title=ranking_message_title, description=ranking_message_txt)
    await message.channel.send(embed=embed)
    
@client.event
async def on_reaction_add(reaction, user):
  #Action relating to pressing one of the buttons to display a runway, fetch all images of a given collection
  if not user.bot and reaction.emoji in emojis:
    #Must grab page number from footer to determine what page we're on and what index to grab
    embed = reaction.message.embeds[0]
    page_number = int(embed.footer.text.split()[1])
    index = (page_number - 1) * 10 + emojis.index(reaction.emoji)

    table = getRunway(reaction.message.embeds[0].title, index)
    runway_url = table['URL'] + "/slideshow/collection"
    response = requests.get(runway_url)
    soup = BeautifulSoup(response.content, "html.parser")

    #Delete message showing all options to avoid spamming buttons and overwhelming backend
    await reaction.message.delete()

    #Gather data where all image urls in the collection are held and convert into json
    results = soup.findAll("script", type="text/javascript", text=True)
    parse = results[1].string
    start = parse.index("runwayGalleries")
    end = parse.index("isMobileDevice")

    #Making usable json from parsed data to easily fetch each image url
    parse = "{" + parse[start - 1:end - 2] + "}"
    ans = json.loads(parse)
    ans = ans["runwayGalleries"]["galleries"][0]["items"]
    
    for n in ans:
      await reaction.message.channel.send(n["image"]["sources"]["xxl"]["url"])
      time.sleep(1)

    rating_embed = discord.Embed(title=str(reaction.message.embeds[0].title + "\n" + table["Collection Title"]), description="Did you enjoy this collection? React with 👍 if you liked the, and 👎 if you didn't.")
    rating_embed.set_footer(text = "Runway #" + str(index+1))
    rating_msg = await reaction.message.channel.send(embed=rating_embed)
    for emoji in vote_emojis:
      await rating_msg.add_reaction(emoji)

  #Action relating to when a user wants to see the page after what is currently displayed in a designer's embed object
  if not user.bot and reaction.emoji == skip_button:
    embed = reaction.message.embeds[0]
    page_number = int(embed.footer.text.split()[1])
    max_page = int(embed.footer.text.split()[3])
    designer_name = embed.title

    #Check and make sure there is a valid page to display
    if (page_number < max_page):
      table = getDesigner(designer_name)
      items = table['Item']['Collections']
      res = ""
      
      #Gather the title and urls of all collections on the page 
      for i in range(10 * page_number, min(10 * (page_number + 1), len(items))):
        run_title = items[i]["Collection Title"]
        res += emojis[i % 10] + " " + run_title + "\n"
      res += "⏭️ for more collections"

      #Add new embed and update message displaying new information
      newEmbed = discord.Embed(title=designer_name, description=res)
      footer_txt = "Page " + str(page_number + 1) + " / " + str(math.ceil(len(items) / 10))
      newEmbed.set_footer(text=footer_txt)
      await reaction.message.edit(embed=newEmbed)
    await reaction.remove(user=user)

  #Action relating to when a user is prompted to upvote or downvote the runway they are currently viewing.
  if not user.bot and reaction.emoji in vote_emojis:
    #Grabbing collection information from backend in order to update information.
    embed = reaction.message.embeds[0]
    designer_name = embed.title.split("\n")[0]
    index = int(embed.footer.text.split("#")[1]) - 1
    table = getRunway(designer_name, index)
    table['TotalVotes'] = table['TotalVotes'] + 1

    #Only increment score when it's an upvote.
    if (reaction.emoji == "👍"):
      table['Score'] = table['Score'] + 1

    #Must call backend and fix information in designer since user input changed a datafield.
    updateRunway(designer_name, index, table)
    
client.run(os.getenv('token'))