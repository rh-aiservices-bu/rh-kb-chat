export class Query {
  content: string;
  collection: string;
  collectionFullName: string;
  selectedVersion: string;
  language: string;
  type = 'Query';

  constructor(
    content: string = '',
    collection: string = '',
    collectionFullName: string = '',
    selectedVersion: string = '',
    language: string = ''
  ) {
    this.content = content;
    this.collection = collection;
    this.collectionFullName = collectionFullName;
    this.selectedVersion = selectedVersion;
    this.language = language;
  }
}

export class Answer {
  content: string[];
  sources: Sources;
  type = 'Answer';

  constructor(content: string[], sources) {
    this.content = content;
    this.sources = sources;
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

export class Sources {
  sourcesArray: Source[];
  type = 'Sources';

  constructor(sources: Source[]) {
    this.sourcesArray = sources;
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
