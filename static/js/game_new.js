const appWidth = 1024;
const appHeight = 800;
const cardHeight = 114;
const cardWidth = 81;
const padding = 10;
const avatarWidth = 200;
const avatarHeight = cardHeight;
const brownColor = 0x765C48;

const bump = new Bump(PIXI);
var texture = PIXI.Texture.from('static/images/card.png');


class GameUX {

    constructor() {
        this.app = new PIXI.Application({width: appWidth, height: appHeight});
        this.renderer = this.app.renderer;
        document.getElementById("new_game").appendChild(this.app.view);
        this.renderStaticElements();
    }

    renderStaticElements() {
        this.app.stage.addChild(this.background());
        this.app.stage.addChild(this.avatar(appWidth/2 - avatarWidth/2, padding));
        this.app.stage.addChild(this.relics(700, padding));
        this.app.stage.addChild(this.inPlayContainer(padding, avatarHeight + padding * 2));
        this.app.stage.addChild(this.inPlayContainer(padding, avatarHeight + cardHeight + padding * 3));

    }

    background() {
        const background = PIXI.Sprite.from(PIXI.Texture.WHITE);
        background.width = appWidth;
        background.height = appHeight;
        background.tint = 0xFFFF00;
        return background;
    }

    avatar(x, y) {
        const avatar = PIXI.Sprite.from(PIXI.Texture.WHITE);
        avatar.width = avatarWidth;
        avatar.height = avatarHeight;
        avatar.tint = brownColor;
        avatar.position.x = x;
        avatar.position.y = y;
        return avatar;
    }

    relics(x, y) {
        const relics = PIXI.Sprite.from(PIXI.Texture.WHITE);
        relics.width = cardWidth * 3;
        relics.height = cardHeight;
        relics.tint = brownColor;
        relics.position.x = x;
        relics.position.y = y;
        return relics;
    }

    inPlayContainer(x, y) {
        const inPlayContainer = PIXI.Sprite.from(PIXI.Texture.WHITE);
        inPlayContainer.width = cardWidth * 7;
        inPlayContainer.height = cardHeight;
        inPlayContainer.tint = brownColor;
        inPlayContainer.position.x = x;
        inPlayContainer.position.y = y;
        return inPlayContainer;
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
    card.scale.set(0.25);
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
