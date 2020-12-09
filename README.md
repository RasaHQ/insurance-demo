# Insurance Starter Pack

## Background

This starter pack is to help get started on insurance related tasks. The starter pack will focus on core insurance functions
as much as possible avoiding functions that are specific to certain types of insurance industries.

## Core Functions

### Update Member Info

- [ ] Update member address. Form is created for this. Need to test on the sample data once it is created.

- [ ] Order a new ID card. Before mailing anything like insurance cards to a member I want to verify their 
address. If the user does not verify their address they should be sent to complete the address change form and then 
directed to resubmit the ID card request verifying their new ID. Still working on the stories for this to do the handoff
between forms, but I think the individual pieces are here.

### Claims

- [ ] Check status of a claim. Users should be able to search their claims and find the status of each. This can be done two ways:

1. User provides the claim id up front in the intent (i.e. what is the status of claim xyz). This is the simplest access
method. On the backend verify if the claim is valid for the user. If it is then provide the details. If not prompt to correct
the ID they provided.

One thing I'm noticing in this workflow is the claim ID entity is validated multiple times if it is invalid... need to
look into some more.

2. User does not provide the claim ID upfront. This is likely the most common use case. User's will be prompted if they 
know the claim id or not. If they don't an assumption is made for this demo pack that they're asking about a recent-ish
claim and recent claims will be displayed.

- [ ] Pay Claim. Users will have the ability to pay a claim. Ideally leverage an existing filled `claim_id` slot. Great
use case to extend the check claim status.

- [ ] Submit a claim. The details here are probably going to need to be specific to an industry, but for this bot could
do something simple like ask how much they're submitting the claim for and a description of why.

### Administrative

- [ ] Get a Quote. Capture basic information from a user to generate a quote for insurance.

- [ ] Find a form. This is a universally terrible UX. Allow users to explain what they are trying to do and serve the correct
form to them. There's a potential that every form in a library could be it's own form in a bot.
