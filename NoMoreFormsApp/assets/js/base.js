Talk.ready.then(function () {
  var me = new Talk.User({
    id: '123456',
    name: 'You',
    email: 'you@example.com',
    photoUrl: 'https://talkjs.com/images/avatar-1.jpg',
    welcomeMessage: 'Hey there! How are you? :-)',
  });
  window.talkSession = new Talk.Session({
    appId: 'tuP7sjEL',
    me: me,
  });
  var other = new Talk.User({
    id: '654321',
    name: 'Jake From State Farm',
    email: 'Sebastian@example.com',
    photoUrl: 'https://talkjs.com/images/avatar-5.jpg',
    welcomeMessage: 'Hey, how can I help?',
  });

  var conversation = talkSession.getOrCreateConversation(
    Talk.oneOnOneId(me, other)
  );
  conversation.setParticipant(me);
  conversation.setParticipant(other);

//  var inbox = talkSession.createInbox({ selected: conversation });
//  inbox.mount(document.getElementById('talkjs-container'));
    var chatbox = window.talkSession.createChatbox();
    chatbox.select(conversation);
    chatbox.mount(document.getElementById('talkjs-container'));
});