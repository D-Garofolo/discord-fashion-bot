import boto3

dynamodb = boto3.resource('dynamodb',region_name='us-east-2')
table = dynamodb.Table('designers')    

#Grab all information about a designer from the backend
def getDesigner(name):
  response = table.get_item(Key={
    'DesignerName': name
  })
  return response

#Add a designer to the backend with their name and the skeleton for all of their collections
def addDesigner(name, collections):
  response = table.put_item(
    Item={
      'DesignerName': name,
      "Collections": collections
    }
  )

#Add images of a specific runway to the backend, use of expression to avoid a hefty write cost
def addRunway(name, index, outfits):
  response = table.update_item(
    Key={
      'DesignerName': name
    },
    UpdateExpression = "SET #cl[" + str(index) + "].#of = :outfits",
    ExpressionAttributeNames={
      "#cl": "Collections",
      "#of": "Outfits"
    },
    ExpressionAttributeValues={
      ":outfits": outfits
    }
  )

#Retrieve a specific collection from the backend, use of expression to avoid a hefty read cost
def getRunway(name, index):
  response = table.get_item(
    Key={
      'DesignerName': name
    },
    ProjectionExpression = "Collections[" + str(index) + "]"
  )
  return response['Item']['Collections'][0]