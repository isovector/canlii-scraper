{-# LANGUAGE LambdaCase        #-}
{-# LANGUAGE OverloadedStrings #-}

module Lib where

import Test.WebDriver
import Test.WebDriver.Commands
import Data.Maybe (fromMaybe, listToMaybe)
import Data.Text (Text)
import qualified Data.Text as T
import Control.Monad (filterM)
import Control.Monad.IO.Class (MonadIO(liftIO))
import Data.Traversable (for)


conf :: WDConfig
conf = useBrowser firefox $ defaultConfig

main :: IO ()
main = runSession conf . finallyClose $ prog


prog :: WD ()
prog = do
  openPage "https://www.canlii.org/en/ca/scc/doc/2020/2020scc39/2020scc39.html"
  clickTab "cited-tab"
  els <- getSelfLinks "decision"
  liftIO $ print els


clickTab :: Text -> WD ()
clickTab tab_id = do
  findElemMaybe (ById tab_id) >>= \case
    Just tab_a -> click tab_a
    Nothing    -> pure ()


getSelfLinks :: Text -> WD [Text]
getSelfLinks cls = do
  els <- findElems $ ByCSS $ "span." <> cls <> " a.canlii"
  for els $ \el -> do
    mhref <- attr el "href"
    pure $ fromMaybe "NOTHING" mhref
    -- pure $ case mhref of
    --   Just href -> and
    --     [ T.isPrefixOf "https://www.canlii.org/en/ca" href
    --     , not $ T.isInfixOf "#" href
    --     ]
    --   Nothing -> False


findElemMaybe :: Selector -> WD (Maybe Element)
findElemMaybe = fmap listToMaybe . findElems

