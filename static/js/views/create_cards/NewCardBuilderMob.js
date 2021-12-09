import React, { Component } from "react";
import * as Constants from '../../constants.js';
import { Card } from '../../components/Card.js';
import { createTheme, ThemeProvider } from '@mui/material/styles';
import NewCardBuilderBase from './NewCardBuilderBase';
import Box from '@mui/material/Box';
import Button from '@mui/material/Button';
import FormControl from '@mui/material/FormControl';
import InputLabel from '@mui/material/InputLabel';
import MenuItem from '@mui/material/MenuItem';
import Select from '@mui/material/Select';
import Slider from '@mui/material/Slider';
import ToggleButton from '@mui/material/ToggleButton';
import ToggleButtonGroup from '@mui/material/ToggleButtonGroup';


class NewCardBuilderMob extends NewCardBuilderBase {
    state = {
        cardType: Constants.mobCardType,
        strength: 0,
        hitPoints: 1,
        manaCost: 0,
        powerPoints: 2,
        effects: [],
        effect: null,
    };

    cardInfo = () => {
        let info = this.baseCardInfo();
        info.cost = this.state.manaCost;
        info.strength = this.state.strength;
        info.hit_points = this.state.hitPoints;
        info.effects = this.state.effects;
        info.power_points = this.state.powerPoints;
        return info;
    };

    nextButtonClicked = async (event) => {
        this.nextOrNewEffectButtonClicked("save_mob", false);
    };

    changeManaCost = (event, value) => {
        this.setState({manaCost: value});
        this.props.cardView.setManaCost(value);
    };

    changeStrength = (event, value) => {
        this.setState({strength: value});
        this.props.cardView.setStrength(value);
    };

    changeHitPoints = (event, value) => {
        this.setState({hitPoints: value});
        this.props.cardView.setHitPoints(value);
    };

    changeEffect = (event, value) => {
        if (!value) {
            this.setState({effect:null, effects:[]});
            this.props.cardView.setEffects([]);
            this.getPowerPoints();
        } else {
            for (let effect of this.props.effectsAndTypes.effects) {
                if (effect.id === value) {
                    this.setState({effect, effects:[effect]}, () => { this.getEffectForInfo(this.state.effect) });
                }
            }            
        }
    };

    changeEffectTrigger = (event) => {
        const effect = this.state.effect;
        effect.effect_type = event.target.value;
        this.setState({effect, effects:[effect]}, () => { this.getEffectForInfo(this.state.effect) });
    };

    changeTargetType = (event) => {
        const effect = this.state.effect;
        effect.target_type = event.target.value;
        this.setState({effect, effects:[effect]}, () => { this.getEffectForInfo(this.state.effect) });
    };

    changeEffectAmount = (event) => {
        const effect = this.state.effect;
        effect.amount = event.target.value;
        this.setState({effect, effects:[effect]});
    };

    effectButtonGroup = () => {
        const effects = this.props.effectsAndTypes.effects.filter(effect => {
                return effect.legal_card_type_ids.includes(this.cardInfo().card_type);
            })

        let unusedOrDuplicableEffects = [];

        for (let effect of effects) {
            let used = false;
            for (let usedEffect of this.state.effects) {
                if (usedEffect.id == effect.id && this.state.effect.id != usedEffect.id) {
                    used = true;
                }
            }
            if (effect.effect_type == "spell" || !used) {
                unusedOrDuplicableEffects.push(effect);
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
                style={{flexWrap:"wrap"}}
                >
                {toggleButtons}
                </ToggleButtonGroup>
        return toggleButtonGroup;
    }

    sliderDiv = (title, ariaLabel, marks, action, onChangeCommitted) => {
        return <div style={{width:"33%"}}>
            <h2>{title}</h2>
            <Box sx={{ width: 120, paddingLeft:"12px", paddingTop: 1 }}>
                <Slider
                  aria-label={title}
                  getAriaValueText={(value) => { return `${value} ${ariaLabel}`; }}
                  defaultValue={0}
                  valueLabelDisplay="auto"
                  step={1}
                  marks={marks}
                  min={0}
                  max={10}
                  onChange={action}
                  onChangeCommitted={onChangeCommitted}
                />
            </Box>
        </div>
    }

    amountSliderDiv = (title, ariaLabel, marks, onChangeCommitted) => {
        return <div>
            <Box sx={{ width: 120, paddingLeft:"12px", paddingTop: 1 }}>
                <Slider
                  aria-label={title}
                  getAriaValueText={(value) => { return `${value} ${ariaLabel}`; }}
                  defaultValue={0}
                  valueLabelDisplay="auto"
                  step={1}
                  marks={marks}
                  min={1}
                  max={10}
                  onChange={this.changeEffectAmount}
                  onChangeCommitted={onChangeCommitted}
                  value={this.state.effect.amount}
                />
            </Box>
        </div>
    }

    amountMarks = (label) => {
        return [
          {
            value: 1,
            label: `1 ${label}`,
          },
          {
            value: 10,
            label: `10 ${label}`,
          },
        ];


    }

    render() {
        const theme = createTheme({
          components: {
            // Name of the component
            MuiSlider: {
              styleOverrides: {
                 markLabel: {
                    transform: 'translateX(-12%)',
                },
              },
            },
          },
        });
        
        const manaMarks = [
          {
            value: 0,
            label: '0 Mana',
          },
          {
            value: 10,
            label: '10 Mana',
          },
        ];

        const strengthMarks = [
          {
            value: 0,
            label: '0 Strength',
          },
          {
            value: 10,
            label: '10 Strength',
          },
        ];

        const hitPointMarks = [
          {
            value: 1,
            label: '1 Hit Point',
          },
          {
            value: 10,
            label: '10 Hit Points',
          },
        ];

            
        let effectTriggerSelect = null;
        let targetTypeSelect = null;
        let amountSlider = null;
        if (this.state.effect) {            
            if (this.state.effect.legal_effect_types) {
                let menuItems = [];
                for (let i=0;i<this.state.effect.legal_effect_types.length;i++) {
                    const trigger = this.state.effect.legal_effect_types[i];
                    menuItems.push(<MenuItem key={i} value={trigger.id}>{trigger.name}</MenuItem>);
                }
                effectTriggerSelect = <FormControl>
                  <InputLabel id="effect-trigger-select-label">Effect Trigger</InputLabel>
                  <Select
                    labelId="effect-trigger-select-label"
                    id="effect-trigger-select"
                    value={this.state.effect.effect_type}
                    label="Effect Trigger"
                    onChange={this.changeEffectTrigger}
                  >
                    {menuItems}
                  </Select>
                </FormControl>;
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
            if (this.state.effect.legal_target_types) {
                let legalTargetTypes = [];
                for (let targetType of this.state.effect.legal_target_types) {
                    if (alreadyHasTargettedEffect && targettedEffectTypes.includes(targetType.id)) {
                        continue;
                    }
                    legalTargetTypes.push(targetType)
                }
                let menuItems = [];
                for (let i=0;i<legalTargetTypes.length;i++) {
                    const targetType = legalTargetTypes[i];
                    menuItems.push(<MenuItem key={i} value={targetType.id}>{targetType.name}</MenuItem>);
                }
                targetTypeSelect = <FormControl>
                  <InputLabel id="target-type-select-label">Target Type</InputLabel>
                  <Select
                    labelId="target-type-select-label"
                    id="target-type-select"
                    value={this.state.effect.target_type}
                    label="Target Type"
                    onChange={this.changeTargetType}
                  >
                    {menuItems}
                  </Select>
                </FormControl>;                
            }
            if ("amount" in this.state.effect) {
                amountSlider = this.amountSliderDiv(this.state.effect.amount_name, this.state.effect.amount_name, this.amountMarks(this.state.effect.amount_name), () => this.getEffectForInfo(this.state.effect));
            } 
        }


        return (
            <ThemeProvider theme={theme}>
                <h1>Create Mob</h1>
                <div style={{display: "flex"}}>
                    {this.sliderDiv("Mana Cost", "Mana", manaMarks, this.changeManaCost, () => this.getPowerPoints())}
                    {this.sliderDiv("Strength", "Strength", strengthMarks, this.changeStrength, () => this.getPowerPoints())}
                    {this.sliderDiv("Hit Points", "Hit Points", hitPointMarks, this.changeHitPoints, () => this.getPowerPoints())}
                </div>
                <br />    

                <h2>Effect</h2>
                {this.effectButtonGroup()}
                <br /><br />
                {effectTriggerSelect}
                <br /><br />
                {targetTypeSelect}
                <br /><br />
                {amountSlider}
                <br /><br />
                <Button 
                    variant="contained"
                    onClick={this.nextButtonClicked}
                >
                    Next
                </Button> 
                <br /><br />     
            </ThemeProvider>
        );
    }
}

export default NewCardBuilderMob;