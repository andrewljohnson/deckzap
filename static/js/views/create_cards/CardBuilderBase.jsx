import React, { Component } from "react";
import * as Constants from '../../constants.js';
import { ThemeProvider } from '@mui/material/styles';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Slider from '@mui/material/Slider';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';
import Typography from '@mui/material/Typography';

class CardBuilderBase extends Component {
    state = {
        cardType: Constants.mobCardType,
        strength: this.props.originalCardInfo.strength ? this.props.originalCardInfo.strength : 0,
        hitPoints: this.props.originalCardInfo.hit_points ? this.props.originalCardInfo.hit_points : 1,
        manaCost: this.props.originalCardInfo.cost ? this.props.originalCardInfo.cost : 0,
        powerPoints: this.props.originalCardInfo.power_points ? this.props.originalCardInfo.power_points : 0,
        effects: this.props.originalCardInfo.effects ? this.props.originalCardInfo.effects : [],
        effect: this.props.originalCardInfo.effects && this.props.originalCardInfo.effects.length > this.props.effectIndex ? this.props.originalCardInfo.effects[this.props.originalCardInfo.effects.length - 1] : null,
        disableAdditionalEffect: true
    };

    baseURL = () => {
        return "/create_card";
    }

    cardInfo = () => {
        let info = this.baseCardInfo();
        info.cost = this.state.manaCost;
        info.strength = this.state.strength;
        info.hit_points = this.state.hitPoints;
        info.effects = this.state.effects;
        info.power_points = this.state.powerPoints;
        info.description = Constants.cardDescription(info);
        return info;
    };

    baseCardInfo = () => {
        let info;
        if (this.props.originalCardInfo) {
            info = this.props.originalCardInfo;
        } else {
            info = {};
        }
        if (!this.props.originalCardInfo || !this.props.originalCardInfo.name) {
            info.name = this.defaultCardName();
        }
        if (!this.props.originalCardInfo || !this.props.originalCardInfo.image) {
            info.image = this.defaultCardImageFilename();
        }
        return info;
    }

    changeEffect = (event, value) => {
        if (!value) {
            let newEffects = this.state.effects;
            newEffects.pop();
            this.setState({effect: null, effects: newEffects}, () => { this.getPowerPoints() });
            this.props.cardView.setProperty("effects", newEffects);
        } else {
            for (let effect of this.props.effectsAndTypes.effects) {
                if (effect.id === value) {
                    let newEffects = this.state.effects;
                    if (newEffects.length === this.props.effectIndex + 1) {
                        newEffects.pop();
                    }
                    if (this.legalTargetTypes(effect).length > 0) {
                        effect.target_type = this.legalTargetTypes(effect)[0].id;
                    }
                    newEffects.push(effect);
                    this.setState({effect, effects:newEffects}, () => { this.getEffectForInfo(this.state.effect) });
                }
            }            
        }
    };

    defaultCardName = () => {
        return "Unnamed Card";
    }

    defaultCardImageFilename = () => {
        return "uncertainty.svg";
    }

    getPowerPoints = async () => {
        const json = await Constants.postData(`${this.baseURL()}/get_power_points`, { card_info: this.cardInfo(), card_id: this.props.cardID });
        if("error" in json) {
            console.log(json); 
            alert("error fetching power points");
        } else {
            this.setState({powerPoints:json.power_points}, this.toggleButtons);
            this.props.cardView.setProperty("power_points", json.power_points);
        }
    }

    getEffectForInfo = async (effect, successFunction=null) => {
        let cardInfo = this.cardInfo();
        // cardInfo.effects = [effect];
        let json = await Constants.postData(`${this.baseURL()}/get_effect_for_info`, { card_info: cardInfo, card_id: this.props.cardID });
        if("error" in json) {
            console.log(json); 
            alert("error fetching effect info");
        } else {
            if (json.server_effect.legal_effect_type) {
                json.server_effect.effect_type = json.server_effect.legal_effect_types[0].id;
            }
            let newEffects = this.state.effects;
            newEffects[newEffects.length - 1] = json.server_effect            
            this.setState({effect:json.server_effect, effects:newEffects, powerPoints:json.power_points}, this.toggleButtons);
            this.props.cardView.setProperty("effects", newEffects);
            this.props.cardView.setProperty("power_points", json.power_points);
            if (successFunction) {
                successFunction();
            }
        }
    }

    toggleButtons = () => {
        this.setState({"disableSave": this.state.powerPoints > 100 || (this.state.effect == null && this.state.cardType != Constants.mobCardType)});
        this.setState({"disableAdditionalEffect": this.state.powerPoints > 100 || this.state.effect == null});        
    }

    nextButtonClicked = async (event) => {
        this.nextOrNewEffectButtonClicked("save_mob", false);
    };

    additionalEffectButtonClicked = async (event) => {
        this.nextOrNewEffectButtonClicked("save_mob", true);
    };

    nextOrNewEffectButtonClicked = async (path, additionalEffectButtonClicked=false) => {
        const json = await Constants.postData(`${this.baseURL()}/${path}`, { card_info: this.cardInfo(), card_id: this.props.cardID })
        if("error" in json) {
            console.log(json); 
            alert("error saving mob card");
        } else {
            if(additionalEffectButtonClicked) {
                window.location.href = `${this.baseURL()}/${this.props.cardID}/effects/${this.state.effects.length}`
            } else {
                window.location.href = `${this.baseURL()}/${this.props.cardID}/name_and_image`
            }
        }
    }

    changeEffectTrigger = (event) => {
        const effect = this.state.effect;
        effect.effect_type = event.target.value;
        const effects = this.state.effects;
        effects[effects.length - 1] = effect;
        this.setState({effect, effects}, () => { this.getEffectForInfo(this.state.effect) });
    };

    changeTargetType = (event) => {
        const effect = this.state.effect;
        effect.target_type = event.target.value;
        const effects = this.state.effects;
        effects[effects.length - 1] = effect;
        this.setState({effect, effects}, () => { this.getEffectForInfo(this.state.effect) });
    };

    changeEffectAmount = (event, value) => {
        const effect = this.state.effect;
        effect.amount = value;
        const effects = this.state.effects;
        effects[effects.length - 1] = effect;
        this.setState({effect, effects});
    };

    effectButtonGroup = () => {
        const effects = this.props.effectsAndTypes.effects.filter(effect => {
                return effect.legal_card_type_ids.includes(this.cardInfo().card_type);
            })

        let unusedOrDuplicableEffects = [];

        for (let effect of effects) {
            let used = false;
            for (let usedEffect of this.state.effects) {
                if (this.state.effect && usedEffect.id === this.state.effect.id) {
                    continue;
                }
                if (usedEffect.id === effect.id && effect.one_per_card) {
                    used = true;
                }
            }
            if (!used) {
                if (this.legalTargetTypes(effect).length > 0) {
                    unusedOrDuplicableEffects.push(effect);
                }
            } 
        }
        const effectNamesAndIDs = unusedOrDuplicableEffects.map(effect => {
                return {name: effect.name, id: effect.id};
        });

        let toggleButtons = [];
        for (let i=0;i<effectNamesAndIDs.length;i++) {
            const effect = effectNamesAndIDs[i];
            toggleButtons.push(
                <ToggleButton key={i} value={effect.id} aria-label={effect.name} style={{margin:10, marginLeft:0, borderRadius:10, border: "1px solid gray"}}>
                    {effect.name}
                </ToggleButton>
            );
        }
        let toggleButtonGroup = 
                 <ToggleButtonGroup
                  value={this.state.effect ? this.state.effect.id : null}
                  exclusive
                  aria-label="effect name"
                onChange={this.changeEffect}
                style={{flexWrap:"wrap", width: 800}}
                >
                {toggleButtons}
                </ToggleButtonGroup>
        return toggleButtonGroup;
    }

    sliderDiv = (title, ariaLabel, marks, onChange, onChangeCommitted, min=0) => {
        return <div style={{width:"33%"}}>
            <h2>{title}</h2>
            <Box sx={{ width: 120, paddingLeft:"12px", paddingTop: 1 }}>
                <Slider
                  aria-label={title}
                  getAriaValueText={(value) => { return `${value} ${ariaLabel}`; }}
                  value={title == "Mana Cost" ? this.state.manaCost
                         : title == "Strength" ? this.state.strength
                         : title == "Hit Points" ? this.state.hitPoints : null}
                  valueLabelDisplay="auto"
                  step={1}
                  marks={marks}
                  min={min}
                  max={10}
                  onChange={onChange}
                  onChangeCommitted={onChangeCommitted}
                />
            </Box>
        </div>
    }

    amountSliderDiv = (title, ariaLabel, marks, onChangeCommitted, max) => {
        return <div style={{marginBottom:20, paddingLeft:"12px"}}>
                <Box sx={{ width: 120}}>
                <Typography id="input-slider" style={{"marginLeft": "-10px", color: "gray", fontSize: "12px"}} gutterBottom>
                    Effect Amount
                </Typography>                
                <Slider
                      aria-label={title}
                      getAriaValueText={(value) => { return `${value} ${ariaLabel}`; }}
                      valueLabelDisplay="auto"
                      step={1}
                      marks={marks}
                      min={1}
                      max={max}
                      onChange={this.changeEffectAmount}
                      onChangeCommitted={onChangeCommitted}
                      value={this.state.effect.amount}
                    />
                </Box>
            </div>;
    }

    amountMarks = (label, max=10) => {
        return [
          {
            value: 1,
            label: `1 ${label}`,
          },
          {
            value: max,
            label: `${max} ${label}`,
          },
        ];
    }

    changeManaCost = (event, value) => {
        this.setState({manaCost: value});
        this.props.cardView.setProperty("cost", value);
    };

    legalTargetTypes = (effect) => {
        if (!effect.legal_target_types) {
            return [];
        }
        const targettedEffectTypes = ["any", "mob", "enemy_mob", "friendly_mob", "player"];
        let alreadyHasTargettedEffect = false;
        for (let effect of this.state.effects) {
            if (effect == this.state.effect) {
                continue;
            }
            if (targettedEffectTypes.includes(effect.target_type)) {
                alreadyHasTargettedEffect = true;
            }
        }
        let legalTargetTypes = [];
        for (let targetType of effect.legal_target_types) {
            if (alreadyHasTargettedEffect && targettedEffectTypes.includes(targetType.id)) {
                continue;
            }
            legalTargetTypes.push(targetType)
        }
        return legalTargetTypes;

    }

    manaMarks = () => {
        return [
            {
                value: 0,
                label: '0 Mana',
            },
            {
                value: 10,
                label: '10 Mana',
            },
        ];
    }

    effectGroup = () => {
        let effectTriggerSelect = null;
        let targetTypeSelect = null;
        let amountSlider = null;
        let effectTriggerMenuItems = [];
        let targetTypeMenuItems = [];
        if (this.state.effect) {            
            if (this.state.effect.legal_effect_types) {
                for (let i=0;i<this.state.effect.legal_effect_types.length;i++) {
                    const trigger = this.state.effect.legal_effect_types[i];
                    effectTriggerMenuItems.push(<MenuItem key={i} value={trigger.id}>{trigger.name}</MenuItem>);
                }
                effectTriggerSelect = 
                <div style={{marginBottom:30}}>
                    <FormControl>
                      <InputLabel id="effect-trigger-select-label">Effect Trigger</InputLabel>
                      <Select
                        labelId="effect-trigger-select-label"
                        id="effect-trigger-select"
                        value={this.state.effect.effect_type}
                        label="Effect Trigger"
                        onChange={this.changeEffectTrigger}
                      >
                        {effectTriggerMenuItems}
                      </Select>
                    </FormControl>
                    <p style={{marginTop:5, marginLeft:4, color: "gray"}}>{this.props.effectsAndTypes.effect_types[this.state.effect.effect_type].description_for_card_creator}</p>
                </div>
            }

            if (this.state.effect.legal_target_types) {
                let legalTargetTypes = this.legalTargetTypes(this.state.effect);
                for (let i=0;i<legalTargetTypes.length;i++) {
                    const targetType = legalTargetTypes[i];
                    targetTypeMenuItems.push(<MenuItem key={i} value={targetType.id}>{targetType.name}</MenuItem>);
                }
                targetTypeSelect = 
                <div style={{marginBottom:20}}>
                    <FormControl>
                      <InputLabel id="target-type-select-label">Target Type</InputLabel>
                      <Select
                        labelId="target-type-select-label"
                        id="target-type-select"
                        value={this.state.effect.target_type}
                        label="Target Type"
                        onChange={this.changeTargetType}
                      >
                        {targetTypeMenuItems}
                      </Select>
                    </FormControl>
                </div>;                
            }
            if ("amount" in this.state.effect && this.state.effect.amount !== null) {
                amountSlider = this.amountSliderDiv(this.state.effect.amount_name, this.state.effect.amount_name, this.amountMarks(this.state.effect.amount_name), () => this.getEffectForInfo(this.state.effect), 10);
                if (this.state.effect.disadvantage_target_types && this.state.effect.disadvantage_target_types.includes(this.state.effect.target_type)) {
                    amountSlider = this.amountSliderDiv(this.state.effect.amount_name, this.state.effect.amount_name, this.amountMarks(this.state.effect.amount_name, this.state.effect.amount_disadvantage_limit), () => this.getEffectForInfo(this.state.effect), this.state.effect.amount_disadvantage_limit);
                }
            } 
        }

        let disableSave = false;
        if (this.state.disableSave) {
            disableSave = true;
        }

        return (
            <ThemeProvider theme={Constants.theme()}>
                <div>
                    <div>
                        <h2>Effect</h2>
                        {this.effectButtonGroup()}
                        <br /><br />
                        {effectTriggerMenuItems.length > 1 && effectTriggerSelect}
                        {targetTypeMenuItems.length > 1 && targetTypeSelect}
                        {amountSlider}
                    </div>
                    <div>
                        {this.props.effectIndex == 0 &&
                            <Button 
                                color="secondary"
                                disabled={this.state.disableAdditionalEffect}
                                variant="contained"
                                onClick={this.additionalEffectButtonClicked}
                                style={{marginRight: 30}}
                            >
                                + Effect
                            </Button> 
                        }
                        <Button 
                            color="primary"
                            disabled={this.state.disableSave}
                            variant="contained"
                            onClick={this.nextButtonClicked}
                        >
                            Choose Name & Image
                        </Button> 
                        {this.state.powerPoints > 100 &&
                            <p style={{color: "red"}}>
                                A card cannot have more than 100 power points.
                            </p> 
                        }
                    </div>
                </div>
            </ThemeProvider>
        );
    }

}


export default CardBuilderBase;