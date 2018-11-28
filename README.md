# storypybotmike

This is an AWS Lambda twitter bot in Python.

Here's what I learned while doing it:

- Lambda doesn't necessarily log all Python exceptions to CloudWatch, so some things may fail "silently." Use try except blocks and log your own exceptions (so make sure you understand how to catch Python Exceptions)

- Set up your test events to submit JSON that's similar to the events that will be calling "for real." I used AWS Event Rules for scheduled execution and thus configured my test event to submit (except with my real account number)
~~~~
{
  "version": "0",
  "detail-type": "Custom Test Event",
  "account": "000000000000",
  "region": "us-east-1",
  "detail": {}
}
~~~~

I chose to read the event like this

~~~~
def lambda_handler(event, _context):
  try:
    if (event["detail-type"] == "Scheduled Event"):
      # "Production" case
    elif (event["detail-type"] == "Custom Test Event"):
      # Test case
    #...
  # except ... ... ...
    # Log failure to read the event
~~~~

I also included a final 

~~~~
if __name__ == "__main__":
~~~~

to also support running locally through the command-line.
