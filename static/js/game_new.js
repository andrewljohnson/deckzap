const appWidth = 1024;
const appHeight = 800;
const cardHeight = 114;
const cardWidth = 81;
const padding = 10;
const avatarHeight = 128;
const avatarWidth = 245;
const brownColor = 0x765C48;
const lightBrownColor = 0xDFBF9F;
const cardContainerWidth = cardWidth * 7 + 12;

const bump = new Bump(PIXI);
var texture = PIXI.Texture.from('static/images/card.png');
var inPlayTexture = PIXI.Texture.from('static/images/in_play.png');
var relicsTexture = PIXI.Texture.from('static/images/relics.png');
var avatarTexture = PIXI.Texture.from('static/images/avatar.png');


class GameUX {

    constructor() {
        this.app = new PIXI.Application({width: appWidth, height: appHeight});
        this.renderer = this.app.renderer;
        document.getElementById("new_game").appendChild(this.app.view);
        this.renderStaticElements();
    }

    renderStaticElements() {
        this.app.stage.addChild(this.background());

        let opponentRow = new PIXI.Container();
        this.app.stage.addChild(opponentRow);
        opponentRow.addChild(this.avatar(cardContainerWidth/2 - avatarWidth/2, padding));
        opponentRow.addChild(this.relics(cardContainerWidth/2 + avatarWidth/2 + padding, padding+6));
        let inPlayAndMenuRow = new PIXI.Container();
        inPlayAndMenuRow.position.x = padding;
        console.log(opponentRow.children[0].height);
        inPlayAndMenuRow.position.y = avatarHeight + padding * 2;
        this.app.stage.addChild(inPlayAndMenuRow);
        inPlayAndMenuRow.addChild(this.inPlayContainer(padding, 0));
        inPlayAndMenuRow.addChild(this.inPlayContainer(padding, padding + cardHeight));
        inPlayAndMenuRow.addChild(this.menu(cardContainerWidth + padding * 2, 0));
        let playerRow = new PIXI.Container();
        playerRow.position.y = inPlayAndMenuRow.position.y + inPlayAndMenuRow.height;
        this.app.stage.addChild(playerRow);
        playerRow.addChild(this.avatar(cardContainerWidth/2 - avatarWidth/2, padding));
        playerRow.addChild(this.relics(cardContainerWidth/2 + avatarWidth/2 + padding, padding+6));

    }

    background() {
        const background = PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.width = appWidth;
        background.height = appHeight;
        background.tint = 0xFFFF00;
        return background;
    }

    avatar(x, y) {
        const avatar = new PIXI.Sprite.from(avatarTexture);
        avatar.scale.set(0.5);
        avatar.position.x = x;
        avatar.position.y = y;
        return avatar;
    }

    relics(x, y) {
        const relics = new PIXI.Sprite.from(relicsTexture);
        relics.scale.set(0.5);
        relics.position.x = x;
        relics.position.y = y;
        return relics;
    }

    inPlayContainer(x, y) {
        const inPlayContainer = new PIXI.Sprite.from(inPlayTexture);
        inPlayContainer.scale.set(0.5);
        inPlayContainer.position.x = x;
        inPlayContainer.position.y = y;
        return inPlayContainer;
    }

    menu(x, y) {
        const menu = PIXI.Sprite.from(PIXI.Texture.WHITE);
        menu.width = 120;
        menu.height = cardHeight * 2 + padding;
        menu.tint = 0x00FF00;
        menu.position.x = x;
        menu.position.y = y;
        return menu;
    }
}

let gameUX = new GameUX();




/*
const handContainer = PIXI.Sprite.from(PIXI.Texture.WHITE);
handContainer.width = cardWidth * 10;
handContainer.height = cardHeight;
handContainer.tint = brownColor;
handContainer.position.x = padding;
handContainer.position.y = renderer.view.height - handContainer.height - padding;
stage.addChild(handContainer);

const gameLog = PIXI.Sprite.from(PIXI.Texture.WHITE);
gameLog.width = appWidth;
gameLog.height = cardHeight *1.25;
gameLog.tint = 0xAAAAAA;
gameLog.position.x = padding;
gameLog.position.y = handContainer.position.y + handContainer.height - padding;
stage.addChild(gameLog);


for (var i = 0; i < 5; i++) {
    createCard(Math.floor(Math.random() * 824) , Math.floor(Math.random() * 640));
}

function createCard(x, y) {
    var card = new PIXI.Sprite(texture);
    // allow it to respond to mouse and touch events
    card.interactive = true;
    // hand cursor appears
    card.buttonMode = true;
    card.scale.set(0.5);
    card.anchor.set(0.5);
    card
        .on('mousedown', onDragStart)
        .on('touchstart', onDragStart)
        // events for drag end
        .on('mouseup', onDragEnd)
        .on('mouseupoutside', onDragEnd)
        .on('touchend', onDragEnd)
        .on('touchendoutside', onDragEnd)
        // events for drag move
        .on('mousemove', onDragMove)
        .on('touchmove', onDragMove);
    card.position.x = x;
    card.position.y = y;
    stage.addChild(card);
}

requestAnimationFrame( animate );

function animate() {
    requestAnimationFrame(animate);
    renderer.render(stage);
}

function onDragStart(event) {
    // store a reference to the data
    // the reason for this is because of multitouch
    // we want to track the movement of this particular touch
    this.data = event.data;
    this.alpha = 0.5;
    this.dragging = true;
}

function onDragEnd() {
    this.alpha = 1;
    this.dragging = false;
    // set the interaction data to null
    this.data = null;
}

function onDragMove() {
    if (this.dragging) {
        var newPosition = this.data.getLocalPosition(this.parent);
        this.position.x = newPosition.x;
        this.position.y = newPosition.y;
    }
}

*/
