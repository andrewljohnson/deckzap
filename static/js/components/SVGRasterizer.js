import * as PIXI from 'pixi.js'
import * as Constants from '../constants.js';


export class SVGRasterizer {

	constructor(app) {		
        // keys for images that have been rendered to the cache already
        this.loadedImageKeys = new Set()
        this.app = app
	}

	loadCardImages(cards) {
        let loadingImages = false;
        for (let card of cards) {
            const loaderURL = this.fullImagePath(card);
            if (this.loadedImageKeys.has(loaderURL)) {
                continue;
            }
            const loaderID = card.name;
            this.loadedImageKeys.add(loaderURL)
            if (!PIXI.utils.TextureCache[loaderID]) {
                loadingImages = true;
                this.loadCardImage(
                    card.card_type,
                    loaderID,
                    loaderURL,
                    );
            }
        }
        return loadingImages;
    }

    fullImagePath(card) {
        let imageName = card.image;
        if (!imageName) {
            imageName = "uncertainty.svg";
        }
        let cardImagesPath = card.is_custom ? Constants.customCardImagesPath : Constants.cardImagesPath;
        return window.location.protocol + "//" + window.location.host + cardImagesPath + imageName;
    }

    loadCardImage(cardType, loaderID, loaderURL) {
        let scale = .5;
        var ua = navigator.userAgent.toLowerCase(); 
        if (ua.indexOf('safari') != -1) { 
          if (ua.indexOf('chrome') > -1) {
          } else {
            scale = .2
          }
        }        

        this.app.loader.add(loaderID, loaderURL, { 
            metadata: {
                resourceOptions: {
                    scale: scale,
                }
            }
        });                       
        this.app.loader.add(loaderID + Constants.largeSpriteQueryString, loaderURL + Constants.largeSpriteQueryString, { 
            metadata: {
                resourceOptions: {
                    scale: scale * 2,
                }
            }
        });                       
    }

}