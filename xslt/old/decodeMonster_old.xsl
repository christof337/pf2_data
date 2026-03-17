<?xml version="1.0" encoding="UTF-8"?>

<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:xp20="http://www.oracle.com/XSL/Transform/java/oracle.tip.pc.services.functions.Xpath20">
    <xsl:template match="/">
        <html>
            <head>
                <style>
                    body {
                    font-family: "ff-good-web-pro", "Open Sans", sans-serif;
                    line-height: 20px;
                    text-align: justify;}
                </style>
            </head>
            <body>
                <xsl:for-each select="monsters/monster">
                    <h1>
                        <div style="float: left; text-transform: uppercase;"><xsl:value-of select="name"/></div>

                        <div style="float: right; text-transform: uppercase;">
                            <xsl:value-of select="type"/>
                            &#160;
                            <xsl:value-of select="level"/>
                        </div>
                    </h1>
                    <br/>
                    <hr/>
                    <xsl:apply-templates select="creatureTraits"/>
                    <xsl:apply-templates select="perception"/>
                    <br/>
                    <xsl:apply-templates select="languages"/>
                    <xsl:if test="languages"><br/></xsl:if>
                    <xsl:apply-templates select="skills"/>
                    <br/>
                    <xsl:apply-templates select="attributes"/>
                    <br/>
                    <xsl:apply-templates select="interactionAbilities"/>
                    <hr/>
                    <xsl:apply-templates select="armorClass"/>
                    <xsl:apply-templates select="saves"/>
                    <br/>
                    <xsl:apply-templates select="health"/>
                    <xsl:apply-templates select="weaknesses"/>
                    <xsl:apply-templates select="immunities"/>
                    <xsl:apply-templates select="resistances"/>
                    <br/>
                    <xsl:apply-templates select="reactiveAbilities"/>
                    <hr/>
                    <xsl:apply-templates select="speeds"/>
                    <br/>
                    <xsl:apply-templates select="strikes"/>
                    <xsl:apply-templates select="offensiveAbilities"/>
                </xsl:for-each>
            </body>
        </html>
    </xsl:template>

    <xsl:template match="creatureTraits">
        <table bgcolor="d8c384">
            <tr style="color:#FFFFFF; font-family:'ff-good-web-pro-condensed', 'Open Sans Condensed', sans-serif !important;
            background-attachment: scroll;
            box-sizing: border-box;
            font-weight: 400;
            margin-bottom: 2.75px;
            margin-top: 2.75px;
            text-transform: uppercase;

          text-rendering: optimizelegibility;">
<!-- background-clip: border-box;
background-color: rgb(86, 97, 147);
background-image: none;
background-origin: padding-box;
background-position-x: 0%;
background-position-y: 0%;
background-repeat: repeat;
background-size: auto;
border-bottom-color: rgb(216, 195, 132);
border-bottom-style: solid;
border-bottom-width: 1.6px;
border-left-color: rgb(216, 195, 132);
border-left-style: solid;
border-left-width: 1.06667px;
border-right-color: rgb(216, 195, 132);
border-right-style: solid;
border-right-width: 1.06667px;
border-top-color: rgb(216, 195, 132);
border-top-style: solid;
border-top-width: 1.6px;
box-sizing: border-box;
color: rgb(255, 255, 255);
display: inline-block;
font-kerning: none;
font-size: 8.8px;
font-weight: 700;
line-height: 8.8px;
min-width: 0px;
padding-bottom: 1.1px;
padding-left: 5.5px;
padding-right: 5.5px;
padding-top: 2.75px;
text-align: center;
text-rendering: optimizelegibility;
-->
                <xsl:for-each select="trait">
                    <xsl:choose>
                        <xsl:when test="@type='size'">
                            <td bgcolor="#497856" style=" padding-bottom: 1.1px;
          padding-left: 5.5px;
          padding-right: 5.5px;
          padding-top: 2.75px;
          text-align: center;">
                                <xsl:value-of select="."/>
                            </td>
                        </xsl:when>
                        <xsl:when test="@type='rarity' and . = 'RARE'">
                            <td bgcolor="#14285e" style=" padding-bottom: 1.1px;
          padding-left: 5.5px;
          padding-right: 5.5px;
          padding-top: 2.75px;
          text-align: center;">
                                <xsl:value-of select="."/>
                            </td>
                        </xsl:when>
                        <xsl:when test="@type='rarity' and . = 'UNIQUE'">
                            <td bgcolor="#14285e" style=" padding-bottom: 1.1px;
          padding-left: 5.5px;
          padding-right: 5.5px;
          padding-top: 2.75px;
          text-align: center;">
                                <xsl:value-of select="."/>
                            </td>
                        </xsl:when>
                        <xsl:otherwise>
                            <td bgcolor="#560D00" style=" padding-bottom: 1.1px;
          padding-left: 5.5px;
          padding-right: 5.5px;
          padding-top: 2.75px;
          text-align: center;">
                                <xsl:value-of select="."/>
                            </td>
                        </xsl:otherwise>
                    </xsl:choose>
                </xsl:for-each>
            </tr>
        </table>
    </xsl:template>
    <xsl:template match="perception">
        <xsl:text>
            <b>Perception&#xA0;</b>
        </xsl:text>
        <xsl:value-of select="bonus"/>
        <xsl:template match="senses">
            <xsl:text> ; </xsl:text>
            <xsl:for-each select="senses/sens">
                <xsl:value-of select="name"/>
                <xsl:if test="precision">&#xA0;(</xsl:if>
                <xsl:value-of select="precision"/>
                <xsl:if test="precision">)&#160;</xsl:if>
                <xsl:value-of select="range"/>
                <xsl:if test="not(position()=last())">, </xsl:if>
            </xsl:for-each>
        </xsl:template>
    </xsl:template>

    <xsl:template match="languages">
        <xsl:choose>
            <xsl:when test="count(language) = 1">
                <xsl:text><b>Langue&#xA0;</b></xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text><b>Langues&#xA0;</b></xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:for-each select="language">
            <xsl:value-of select="."/>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
        <xsl:if test="@cannotTalk='TRUE'">
            <xsl:text> (incapable de parler)</xsl:text>
        </xsl:if>
        <xsl:text>.</xsl:text>
    </xsl:template>

    <xsl:template match="skills">
        <xsl:choose>
            <xsl:when test="count(skill) = 1">
                <xsl:text><b>Compétence </b></xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text><b>Compétences </b></xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:for-each select="skill">
            <xsl:value-of select="name"/><xsl:text>&#xA0;</xsl:text>
            <xsl:value-of select="bonus"/>
            <xsl:if test="skillSpecial">
                <xsl:text> (</xsl:text>
                <xsl:value-of select="skillSpecial"/>
                <xsl:text>)</xsl:text>
            </xsl:if>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="attributes">
        <xsl:text><b>FOR </b></xsl:text> <xsl:value-of select="@STR"/>
        <xsl:text>, <b>DEX </b></xsl:text> <xsl:value-of select="@DEX"/>
        <xsl:text>, <b>CON </b></xsl:text> <xsl:value-of select="@CON"/>
        <xsl:text>, <b>INT </b></xsl:text> <xsl:value-of select="@INT"/>
        <xsl:text>, <b>SAG </b></xsl:text> <xsl:value-of select="@WIS"/>
        <xsl:text>, <b>CHA </b></xsl:text> <xsl:value-of select="@CHA"/>
    </xsl:template>
    
    <xsl:template match="interactionAbilities">
        <xsl:for-each select="special">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="special">
        <b><xsl:value-of select="name"/></b>
        <xsl:choose>
            <xsl:when test="@type='reaction'">
                <!--<xsl:text> [reaction]</xsl:text>-->
                <xsl:text>&#xA0;↩</xsl:text>
            </xsl:when>
            <xsl:when test="@type='activity' and @actions=0">
               <xsl:text>&#xA0;◇ </xsl:text>
            </xsl:when>
            <xsl:when test="@type='activity' and @actions=1">
                <!--<xsl:text> [</xsl:text><xsl:value-of select="@actions"/><xsl:text> action</xsl:text><xsl:if test="@actions>1">s</xsl:if><xsl:text>] </xsl:text>-->
                <!--<xsl:value-of select="string-join(for $i in 1 to @actions return '◆', '')"/>-->
                <xsl:text>&#xA0;◆ </xsl:text>
            </xsl:when>
            <xsl:when test="@type='activity' and @actions=2">
               <xsl:text>&#xA0;◆◆ </xsl:text>
            </xsl:when>
            <xsl:when test="@type='activity' and @actions=3">
                <xsl:text>&#xA0;◆◆◆ </xsl:text>
            </xsl:when>
        </xsl:choose>
        <xsl:apply-templates select="traits"/>
        <xsl:if test="not(@type='activity') and not(@type='reaction')">
            <xsl:text>.&#xA0;</xsl:text>
        </xsl:if>
        <xsl:if test="traits and withDot='TRUE'">. </xsl:if>
        <xsl:if test="frequency">
            <b> Fréquence </b>
            <xsl:value-of select="frequency"/> ;
        </xsl:if>
        <xsl:if test="requirements">
            <b> Conditions. </b><xsl:value-of select="requirements"/> ;
        </xsl:if>
        <xsl:if test="trigger">
            <xsl:text><b> Déclencheur. </b></xsl:text>
            <xsl:value-of select="trigger"/> ;
        </xsl:if>
        <xsl:if test="effect">
            <xsl:text><b>Effet. </b></xsl:text>
            <xsl:copy>
                <xsl:apply-templates select="effect"/>
            </xsl:copy>
           <!-- <xsl:value-of select="effect"/>-->
        </xsl:if>
        <xsl:if test="description">
            <xsl:apply-templates select="description"/>
        </xsl:if>
        <br/>
    </xsl:template>

    <xsl:template match="description">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()"/>
        </xsl:copy>
        <!--<xsl:choose>
            <xsl:when test="scseecBloc">
                <xsl:value-of select="beforeBloc"/><br/>
                <xsl:apply-templates select="scseecBloc"/>
                <xsl:value-of select="afterBloc"/>
            </xsl:when>
            <xsl:otherwise>
                <xsl:value-of select="."/>
            </xsl:otherwise>
        </xsl:choose>-->
    </xsl:template>

    <xsl:template match="armorClass">
        <xsl:text><b>CA </b></xsl:text>
        <xsl:value-of select="."/>
        <xsl:text> ;</xsl:text>
    </xsl:template>

    <xsl:template match="saves">
        <xsl:text> <b>Réf </b></xsl:text> <xsl:value-of select="@REF"/>
        <xsl:text>, <b>Vig </b></xsl:text> <xsl:value-of select="@FOR"/>
        <xsl:text>, <b>Vol </b></xsl:text> <xsl:value-of select="@VOL"/>
        <xsl:if test="@saveSpecial">
            <xsl:text> ; </xsl:text>
            <xsl:value-of select="@saveSpecial"/>
        </xsl:if>
    </xsl:template>

    <xsl:template match="health">
        <xsl:text><b>PV </b></xsl:text>
        <xsl:value-of select="."/>
    </xsl:template>

    <xsl:template match="weaknesses">
        <xsl:choose>
            <xsl:when test="count(weakness) = 1">
                <xsl:text> ; <b>Faiblesse </b></xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text> ; <b>Faiblesses </b></xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:for-each select="weakness">
            <xsl:value-of select="name"/><xsl:text>&#xA0;</xsl:text>
            <xsl:value-of select="value"/>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="immunities">
        <xsl:choose>
            <xsl:when test="count(immunity) = 1">
                <xsl:text> ; <b>Immunité </b></xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text> ; <b>Immunités </b></xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:for-each select="immunity">
            <xsl:value-of select="."/>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="resistances">
        <xsl:choose>
            <xsl:when test="count(resistance) = 1">
                <xsl:text> ; <b>Résistance </b></xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text> ; <b>Résistances </b></xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:for-each select="resistance">
            <xsl:value-of select="name"/><xsl:text>&#xA0;</xsl:text>
            <xsl:value-of select="value"/>
            <xsl:if test="exceptions">
                <xsl:text> (sauf </xsl:text>
                <xsl:for-each select="exceptions/exception">
                    <xsl:value-of select="."/>
                    <xsl:if test="not(position()=last())">, </xsl:if>
                </xsl:for-each>
                <xsl:text>)</xsl:text>
            </xsl:if>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="reactiveAbilities">
        <xsl:for-each select="special">
            <xsl:apply-templates select="."/>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="speeds">
        <xsl:choose>
            <xsl:when test="count(speed) = 1">
                <xsl:text><b>Vitesse </b></xsl:text>
            </xsl:when>
            <xsl:otherwise>
                <xsl:text><b>Vitesses </b></xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:for-each select="speed">
            <xsl:choose>
                <xsl:when test="@type='climb'">
                    escalade
                </xsl:when>
                <xsl:when test="@type='swim'">
                    nage
                </xsl:when>
                <xsl:when test="@type='burrow'">
                    creusement
                </xsl:when>
                <xsl:when test="@type='fly'">
                    vol
                </xsl:when>
            </xsl:choose>
            <xsl:value-of select="."/>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
        <xsl:if test="@speedSpecial">
            <xsl:text> ; </xsl:text>
            <xsl:value-of select="@speedSpecial"/>
        </xsl:if>
    </xsl:template>

    <xsl:template match="strike">
        <xsl:choose>
            <xsl:when test="@type='melee'">
                <xsl:text><b>Corps à corps </b></xsl:text>
            </xsl:when>
            <xsl:when test="@type='ranged'">
                <xsl:text><b>À distance </b></xsl:text>
            </xsl:when>
        </xsl:choose>
<!--        <xsl:text>[1 action] </xsl:text>-->
        <xsl:text>◆ </xsl:text>
        <xsl:value-of select="name"/><xsl:text>&#xA0;</xsl:text>
        <xsl:value-of select="bonus"/><xsl:if test="traits">&#xA0;</xsl:if>
        <xsl:apply-templates select="traits"/>
        <xsl:text>, </xsl:text>
        <xsl:apply-templates select="damages"/>
        <xsl:for-each select="extras/extra">
            <xsl:text> plus </xsl:text>
            <xsl:value-of select="."/>
        </xsl:for-each>
        <br/>
    </xsl:template>

    <xsl:template match="traits">
        <xsl:text> (</xsl:text>
        <xsl:for-each select="trait">
            <xsl:value-of select="."/>
            <xsl:if test="not(position()=last())">, </xsl:if>
        </xsl:for-each>
        <xsl:text>)</xsl:text>
    </xsl:template>

    <xsl:template match="damages">
        <xsl:text><b>Dégâts </b></xsl:text>
        <xsl:for-each select="damage">
            <xsl:if test="position()>1"> plus </xsl:if>
            <xsl:value-of select="amount"/><xsl:text>&#xA0;</xsl:text>
            <xsl:value-of select="damageType"/>
        </xsl:for-each>
    </xsl:template>

    <xsl:template match="scseecBloc">
        <br/>
        <xsl:if test="criticalSuccess">
            <b>Succès critique. </b><xsl:value-of select="criticalSuccess"/>
            <br/>
        </xsl:if>
        <xsl:if test="success">
            <b>Succès. </b><xsl:value-of select="success"/>
            <br/>
        </xsl:if>
        <xsl:if test="failure">
            <b>Échec. </b><xsl:value-of select="failure"/>
            <br/>
        </xsl:if>
        <xsl:if test="criticalFailure">
            <b>Échec critique. </b><xsl:value-of select="criticalFailure"/>
        </xsl:if>
    </xsl:template>

    <xsl:template match="spell">
        <i><xsl:value-of select="."/></i>
        <!-- specify the source of the spell between brackets, if any -->
        <xsl:if test="@source"><xsl:text> (</xsl:text><xsl:value-of select="@source"/><xsl:text>)</xsl:text> </xsl:if>
        <!-- specify special indication, such as "at will" between brackets, if any -->
        <xsl:if test="@spellSpecial"><xsl:text> (</xsl:text><xsl:value-of select="@spellSpecial"/><xsl:text>)</xsl:text> </xsl:if>
    </xsl:template>

    <xsl:template match="list">
        <ul>
        <xsl:for-each select="listItem">
            <li><xsl:apply-templates select="."/></li>
        </xsl:for-each>
        </ul>
    </xsl:template>

    <xsl:template match="table">
        <table style="border-collapse: collapse;
box-sizing: border-box;
color: rgb(34, 34, 34);
margin-top: 0px;
text-align: left;">
            <xsl:if test="headerLine">
                <tr style="background: #5D0000 !important;
  color: #fff !important;">
                    <xsl:for-each select="headerLine/cell">
                        <th><xsl:value-of select="."/></th>
                    </xsl:for-each>
                </tr>
            </xsl:if>
            <xsl:for-each select="line">
                <xsl:choose>
                    <xsl:when test="position() mod 2 =0">
                        <tr style="background: #EDE3C7 !important">
                            <xsl:for-each select="cell">
                                <td><xsl:value-of select="."/></td>
                            </xsl:for-each>
                        </tr>
                    </xsl:when>
                    <xsl:otherwise>
                        <tr style="background: #F4EEE0 !important">
                            <xsl:for-each select="cell">
                                <td><xsl:value-of select="."/></td>
                            </xsl:for-each>
                        </tr>
                    </xsl:otherwise>
                </xsl:choose>
            </xsl:for-each>
        </table>
    </xsl:template>

    <xsl:template match="spellList">
        <xsl:text><b>Sorts </b></xsl:text>
        <xsl:choose>
            <xsl:when test="@source='innate'"><b>innés </b></xsl:when>
        </xsl:choose>
        <xsl:choose>
            <xsl:when test="@tradition='primal'"><b>primordiaux </b></xsl:when>
        </xsl:choose>
        <xsl:text>DD </xsl:text>
        <xsl:value-of select="@DD"/>
        <xsl:text> ; </xsl:text>
        <xsl:for-each select="rank">
            <b>
            <xsl:choose>
                <xsl:when test="@constant='TRUE'"><xsl:text>Constant (</xsl:text><xsl:value-of select="@rank"/><sup>e</sup></xsl:when>
                <xsl:when test="@cantrips='TRUE'"><xsl:text>Tours de magie (</xsl:text><xsl:value-of select="@rank"/><sup>e</sup></xsl:when>
                <xsl:when test="@rank"><xsl:value-of select="@rank"/><sup>e</sup></xsl:when>
            </xsl:choose>
            </b>
            <xsl:for-each select="spells">
                <xsl:apply-templates select="spell"/>
                <xsl:if test="not(position()=last())">, </xsl:if>
            </xsl:for-each>
            <xsl:if test="not(position()=last())"> ; </xsl:if>
        </xsl:for-each>
    </xsl:template>
</xsl:stylesheet>