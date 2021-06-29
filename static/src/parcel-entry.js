import { GameUX } from '../js/game';
import { GameRoom } from '../js/GameRoom';

const gameUX = new GameUX();
const gameRoom = new GameRoom(gameUX);
gameRoom.connect();


// import './scss/index.scss';