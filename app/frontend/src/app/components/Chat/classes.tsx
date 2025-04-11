export class Query {
  content: string;
  collection: string;
  collectionFullName: string;
  selectedVersion: string;
  language: string;
  timestamp: Date;
  type = 'Query';
  
  constructor(
    content: string = '',
    collection: string = '',
    collectionFullName: string = '',
    selectedVersion: string = '',
    language: string = '',
    timestamp: Date = new Date()
  ) {
    this.content = content;
    this.collection = collection;
    this.collectionFullName = collectionFullName;
    this.selectedVersion = selectedVersion;
    this.language = language;
    this.timestamp = timestamp;
  }
}

export class Answer {
  content: string[];
  sources: Source[];
  timestamp: Date;
  type = 'Answer';
  
  constructor(content: string[], sources, timestamp) {
    this.content = content;
    this.sources = sources;
    this.timestamp = timestamp;
  }
}

export class Source {
  content: string;
  score: number;

  constructor(content: string, score: number) {
    this.content = content;
    this.score = score;
  }
}

export class MessageContent {
  messageContent: Query | Answer ;
  
  constructor(messageContent: Query | Answer ) {
    this.messageContent = messageContent;
  }
}

export class MessageHistory {
  message: MessageContent[];

  constructor(message: MessageContent[]) {
    this.message = message;
  }
}

export class Models {
  name: string;

  constructor(name: string) {
    this.name = name;
  }
}
